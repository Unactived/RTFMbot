import asyncpg
from functools import partialmethod

class Database:
    @classmethod
    async def create(self, uri):
        """Factory method to create an instance through an async context"""

        self = Database()

        self.pool = await asyncpg.create_pool(uri)

        return self

    async def init(self):

        async with self.pool.acquire() as conn:
            async with conn.transaction():

                return await conn.fetch('SELECT * FROM guilds'), await conn.fetch('SELECT id,blacklisted FROM users')

    async def _retrieve_values(self, table, id, cols):

        async with self.pool.acquire() as conn:
            async with conn.transaction():

                # cols is a string or a collection of strings
                if isinstance(cols, str):
                    return await conn.fetchval(f'SELECT {cols} FROM {table} WHERE id=$1', id)

                fields = ','.join(cols)
                row = await conn.fetchrow(f'SELECT {fields} FROM {table} WHERE id=$1', id)

                return [row[col] for col in cols]

    get_from_guild = partialmethod(_retrieve_values, 'guilds')
    get_from_user  = partialmethod(_retrieve_values, 'users')

    async def _set_values(self, table, id, cols, vals):

        async with self.pool.acquire() as conn:
            async with conn.transaction():

                if isinstance(cols, str):
                    await conn.execute(f'INSERT INTO {table}(id,{cols}) VALUES($2,$1) ON CONFLICT (id) DO UPDATE SET {cols}=$1', vals, id)
                    return

                # this is the part where I make some funny comment about how the following is horrible

                fields = ','.join(cols)
                values = ','.join(vals)

                n = len(vals)

                statement = f'INSERT INTO {table}(id,{fields}) VALUES($1'

                for i in range(2,n+2):
                    statement += f',${i}'

                statement += ') ON CONFLICT (id) DO UPDATE SET '

                for col,i in zip(cols, range(2, n+2)):
                    statement += f'{col}=${i},'

                args = [id]
                args.extend(vals)

                await conn.execute(statement[:-1], *args) # pop last comma

    set_in_guild = partialmethod(_set_values, 'guilds')
    set_in_user  = partialmethod(_set_values, 'users')