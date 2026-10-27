import asyncio
from asyncua import Server, ua

async def main():
    server = Server()
    await server.init()
    # السيرفر يعمل على المنفذ 4840
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)
    
    # إنشاء كائن (كأنه آلة)
    myobj = await server.nodes.objects.add_object(idx, "Machine")
    myvar = await myobj.add_variable(idx, "Production_Count", 0)
    await myvar.set_writable()

    print("✅ السيرفر يعمل على: opc.tcp://0.0.0.0:4840")
    
    async with server:
        count = 0
        while True:
            await asyncio.sleep(2) # كل ثانيتين
            count += 1 # زيادة الإنتاج
            await myvar.write_value(count)
            print(f"📈 تم تحديث قيمة الإنتاج إلى: {count}")

if __name__ == "__main__":
    asyncio.run(main())
