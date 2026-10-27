$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$campaign=Join-Path $workspace 'artifacts\runner-readiness-next-twenty-project-pass'
$target=Join-Path $campaign 'active\cargo-generate'
$relative='home\appdata\Local\Microsoft\Windows\INetCache\Content.IE5'
$linkPath=Join-Path $target $relative
$destination=Join-Path $target 'home\appdata\Local\Microsoft\Windows\INetCache\IE'
$link=Get-Item -LiteralPath $linkPath -Force
if (-not ($link.Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Expected exact owned Windows cache reparse point'}
# Windows PowerShell5.1 does not expose LinkType/Target for this legacy INetCache
# mount point. Read its actual reparse buffer without following the link.
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;
public static class OwnedCacheReparse {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern SafeFileHandle CreateFile(string path,uint access,uint share,IntPtr security,uint creation,uint flags,IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool DeviceIoControl(SafeFileHandle handle,uint code,IntPtr input,uint inputSize,byte[] output,uint outputSize,out uint returned,IntPtr overlapped);
    public static string ReadMountPoint(string path) {
        using (var handle=CreateFile(path,0,7,IntPtr.Zero,3,0x02200000,IntPtr.Zero)) {
            if(handle.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
            var data=new byte[16384];uint size;
            if(!DeviceIoControl(handle,0x900a8,IntPtr.Zero,0,data,(uint)data.Length,out size,IntPtr.Zero)) throw new Win32Exception(Marshal.GetLastWin32Error());
            if(size<16 || BitConverter.ToUInt32(data,0)!=0xa0000003) throw new InvalidOperationException("Expected mount-point reparse tag");
            int offset=BitConverter.ToUInt16(data,8),length=BitConverter.ToUInt16(data,10);
            if((length%2)!=0 || 16+offset+length>size) throw new InvalidOperationException("Invalid mount-point buffer");
            return Encoding.Unicode.GetString(data,16+offset,length);
        }
    }
}
'@
$actualTarget=[OwnedCacheReparse]::ReadMountPoint($linkPath)
if ($actualTarget.StartsWith('\??\') -or $actualTarget.StartsWith('\\?\')) {$actualTarget=$actualTarget.Substring(4)}
if ([IO.Path]::GetFullPath($actualTarget) -ne $destination -or (Resolve-Path -LiteralPath $destination).ProviderPath -ne $destination) {throw 'Cache junction destination differs from exact owned cache'}
foreach($starting in @([IO.Path]::GetDirectoryName($linkPath),$destination)) {
    $checked=$starting
    while($checked -ne $workspace) {
        if (-not $checked.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase) -or
            ((Get-Item -LiteralPath $checked -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Unsafe cache link ancestor/destination'}
        $checked=[IO.Path]::GetDirectoryName($checked)
    }
}
function Get-DestinationInventory {
    $files=@{};$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($destination);$total=[long]0
    while($pending.Count) {
        foreach($entry in Get-ChildItem -LiteralPath $pending.Dequeue() -Force) {
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Linked cache junction destination payload'}
            if ($entry.PSIsContainer) {$pending.Enqueue($entry.FullName);continue}
            $total+=$entry.Length
            if ($files.Count -ge 5000 -or $total -gt 67108864) {throw 'Cache destination inventory bound'}
            $files[$entry.FullName.Substring($destination.Length+1)]=@{bytes=$entry.Length;sha256=(Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
        }
    }
    return $files
}
$before=Get-DestinationInventory
# Nonrecursive native DirectoryInfo.Delete removes only the junction itself.
# It cannot recursively erase the destination; all paths stay in this shell.
$link.Delete()
if (Test-Path -LiteralPath $linkPath) {throw 'Cache junction remains'}
$after=Get-DestinationInventory
if ($before.Count -ne $after.Count) {throw 'Junction destination file coverage changed'}
foreach($name in $before.Keys) {
    if ($after[$name].bytes -ne $before[$name].bytes -or $after[$name].sha256 -ne $before[$name].sha256) {throw 'Cache junction destination bytes changed'}
}
$receipt=Join-Path $campaign 'cargo-generate\windows-cache-junction-removed.json'
if (Test-Path -LiteralPath $receipt) {throw 'Preserve existing junction removal record'}
@{schema_version=1;owned_target=$target;removed_link=$relative;destination='home/appdata/Local/Microsoft/Windows/INetCache/IE';
    exact_owned_junction_unlinked=$true;destination_unchanged=$true;destination_files=$before;checked_at_utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receipt -Encoding UTF8
Write-Output 'Exact owned INetCache junction removed nonrecursively; destination file bytes and directory preserved.'
