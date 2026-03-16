import socket

hosts = ["google.com", "db.qnpvqmqkknhxycpseqir.supabase.co", "db.qnpvqmqkknhxycpseqir.supabase.com", "qnpvqmqkknhxycpseqir.supabase.co"]

for host in hosts:
    try:
        ip = socket.gethostbyname(host)
        print(f"Host: {host} -> Resolved IP: {ip}")
    except Exception as e:
        print(f"Host: {host} -> Resolution Error: {e}")
