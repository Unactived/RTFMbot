# Mainly from:
# https://codereview.stackexchange.com/a/182926
import gzip
import io
import json
import zlib
from functools import partial
from typing import NamedTuple, AnyStr, Union, List, Optional, Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

bytes_ = partial(bytes, encoding='utf-8')

_TioFile = NamedTuple(
    '_TioFile',
    [
        ('name', AnyStr),
        ('content', bytes)
    ]
)
_TioVariable = NamedTuple(
    '_TioVariable',
    [
        ('name', AnyStr),
        ('content', Union[List[AnyStr], AnyStr])
    ]
)
_TioResult = NamedTuple(
    '_TioResult',
    [
        ('output', Union[AnyStr, object]),
        ('debug', Union[AnyStr, object])
    ]
)
_TioResponse = NamedTuple(
    '_TioResponse',
    [
        ('code', Union[AnyStr, int]),
        ('result', Union[AnyStr, None]),
        ('error', Union[AnyStr, None]),
    ]
)


class TioFile(_TioFile):
    def as_bytes(self):
        content = self.content
        if isinstance(content, str):
            length = len(content.encode('utf-8'))
        elif isinstance(content, (str, bytes, bytearray)):
            length = len(content)
        else:
            raise ValueError("Can only pass UTF-8 strings or bytes at this time.")

        return bytes_(
            'F{name}\x00{length}\x00{content}\x00'
                .format(
                    name=self.name,
                    length=length,
                    content=self.content
                )
            )


class TioVariable(_TioVariable):
    def as_bytes(self):
        return bytes_(
            'V{name}\x00{length}\x00{content}\x00'
                .format(
                    name=self.name,
                    length=len(self.content.split(' ')),
                    content=self.content
                )
            )


class TioResult(_TioResult):
    EMPTY = object()

    @staticmethod
    def new(output=EMPTY, debug=EMPTY):
        return TioResult(output, debug)


class TioResponse(_TioResponse):
    @staticmethod
    def from_raw(code, data=None, error=None):
        if data is None:
            splitdata = [None, error]
        else:
            splitdata = data.split(data[:16])

        if not splitdata[1] or splitdata[1] == b'':
            error = b''.join(splitdata[2:])
            result = None
        else:
            error = None
            result = splitdata[1]

        if result is not None:
            result = result.decode('utf-8')

        if error is not None:
            error = error.decode('utf-8')
        return TioResponse(code, result, error, data)

class TioRequest:
    def __init__(self, lang, code):
        self._files = []
        self._variables = []

        self.set_lang(lang)
        self.set_code(code)

    def set_code(self, code):
        self.add_file_bytes('.code.tio', code)

    def add_variable(self, variable):
        self._variables.append(variable)

    def add_variable_string(self, name, value):
        self._variables.append(TioVariable(name, value))

    def add_file_bytes(self, name, content):
        self._files.append(TioFile(name, content))

    def set_lang(self, lang):
        self.add_variable_string('lang', lang)

    def as_bytes(self):
        bytes_ = bytes()
        try:
            for var in self._variables:
                if var.content:
                    bytes_ += var.as_bytes()
            for file in self._files:
                bytes_ += file.as_bytes()
            bytes_ += b'R'
        except IOError:
            raise RuntimeError("IOError generated during bytes conversion.")
        return bytes_

    def as_deflated_bytes(self):
        # This returns a DEFLATE-compressed bytestring, which is what TIO.run's API requires for the request
        # to be proccessed properly.
        return zlib.compress(self.as_bytes(), 9)[2:-4]

class Tio:
    backend = "cgi-bin/run/api/"
    json = "languages.json"

    def __init__(self, url="https://tio.run"):
        self.backend = url + '/' + self.backend
        self.json = url + '/' + self.json

    @staticmethod
    def read_in_chunks(stream_object, chunk_size=1024):
        """Lazy function (generator) to read a file piece by piece.
        Default chunk size: 1k."""
        while True:
            data = stream_object.read(chunk_size)
            if not data:
                break
            yield data

    def query_languages(self):
        # Used to get a set containing all supported languages on TIO.run.
        try:
            response = urlopen(self.json)
            rawdata = json.loads(response.read().decode('utf-8'))
            return set(rawdata.keys())
        except (HTTPError, URLError):
            return set()
        except Exception:
            return set()

    def send(self, fmt):
        # Command alias to use send_bytes; this is more or less a TioJ cutover.
        return self.send_bytes(fmt.as_deflated_bytes())

    def send_bytes(self, message):
        req = urlopen(self.backend, data=message)
        reqcode = req.getcode()
        if req.code == 200:
            content_type = req.info().get_content_type()

            # Specially handle GZipped responses from the server, and unzip them.
            if content_type == 'application/octet-stream':
                buf = io.BytesIO(req.read())
                gzip_f = gzip.GzipFile(fileobj=buf)
                fulldata = gzip_f.read()
            else:
                # However, if it's not compressed, just read it directly.
                fulldata = req.read()

            # Return a TioResponse object, containing the returned data from TIO.
            return TioResponse(reqcode, fulldata, None)
        else:
            # If the HTTP request failed, we need to give a TioResponse object with no data.
            return TioResponse(reqcode, None, None)
