import asyncio

async def echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    print('Opened a new connection')
    try:
        while True:
            message: bytes = await reader.readline()
            message_str: str = message.decode().replace('\r', '').replace('\n', '')

            print(f'Got message: {message_str}')

            if message_str in ['quit', '', 'q']:
                writer.write(b'Bye bye\n\r')
                await writer.drain() 
                break

            writer.write(message.upper())
            # Drain нужен для того, чтоб убедиться что запись 
            # в сокет проведена, т.к. может записаться в буфер
            await writer.drain() 

    except asyncio.CancelledError:
        writer.write(b'Sorry, server is shutting down. Your connection will be closed\r\n')
        writer.write_eof()
        await writer.drain()
        print('Task was cancelled')

    finally:
        print('Leaving connection')
        # raise Exception('Test exception')
        # Закрывать reader не нужно.
        writer.close()

loop = asyncio.get_event_loop()
# В данном случае echo будет создаваться для каждого нового коннекта
server_coro = asyncio.start_server(echo, '127.0.0.1', 8888, loop=loop)

# Дожидаемся успешного запуска сервера
server = loop.run_until_complete(server_coro)
print('Server started')

try:
    # Крутим сервер, пока не выключим
    loop.run_forever()
except KeyboardInterrupt:
    print('Shutting down server')

# Graceful shutdown
# Перестаем принимать новые соединения 
server.close()

# Дожидаемся пока они закроются (не затрагивает уже открытые!)
loop.run_until_complete(server.wait_closed())

# Получаем все текущие таски на event loop'e
tasks = asyncio.Task.all_tasks()

# Посылаем всем таскам сигнал на отмену (это будет в виде CanceledError exception)
for task in tasks:
    task.cancel()

# Собираем все таски в одну группу, return_exceptions - нужен для того, 
# чтоб exception произошедший в одной таске не остановил полностью loop и остальные таски закончились
# ака Promise.allSetteled в Node.js
group = asyncio.gather(*tasks, return_exceptions=True)

# Дожидаемся завершения всех задач в группе
results = loop.run_until_complete(group)
# Из-за return_exception=True можем проверить что в results нет объектов подкласса Exception
for res in results:
    if isinstance(res, Exception):
        print(f'Error during shutdown: {res}')

# Закрываем loop
loop.close()




