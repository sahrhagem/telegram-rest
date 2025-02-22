async def check_entity():
    async with client:
        try:
            entity = await client.get_entity(CHANNEL_ID)
            print(f"Entity Found: {entity}")
        except ValueError as e:
            print(f"Error: {e}")

client.loop.run_until_complete(check_entity())