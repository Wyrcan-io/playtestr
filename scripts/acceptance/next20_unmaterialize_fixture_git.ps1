param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z][a-z0-9-]{0,63}$')][string]$Project)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$package=Join-Path $workspace ('docs\validation\runner-readiness-next-twenty-project-pass\'+$Project)
$declaration=Get-Content -LiteralPath (Join-Path $package 'fixture-git.json') -Raw | ConvertFrom-Json
$fixtureRoots=@('fixture')
if($null -ne $declaration.fixture_roots){$fixtureRoots=@($declaration.fixture_roots)}
foreach($relative in $fixtureRoots){
    if($relative -notmatch '^(fixture|fixtures/[a-zA-Z0-9_-]+)$'){throw 'Unsafe fixture Git root'}
    $expected=[IO.Path]::GetFullPath((Join-Path $package ($relative+'/.git')))
    if(-not $expected.StartsWith($package+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture Git root escapes package'}
    if(-not(Test-Path -LiteralPath $expected)){continue}
    $target=(Resolve-Path -LiteralPath $expected).ProviderPath
    if($target -ne $expected){throw 'Unexpected resolved fixture Git root'}
    $ancestor=$target
    while($ancestor -ne $workspace){
        if((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked fixture ancestor'}
        $ancestor=[IO.Path]::GetDirectoryName($ancestor)
    }
    $actual=@{};$directories=@{};$pending=[Collections.Generic.Queue[string]]::new();$pending.Enqueue($target)
    while($pending.Count){
        foreach($entry in Get-ChildItem -LiteralPath $pending.Dequeue() -Force){
            if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked fixture Git entry'}
            $name=$entry.FullName.Substring($target.Length+1).Replace('\','/')
            if($entry.PSIsContainer){
                if($name -notin @($declaration.directories)){throw 'Unknown fixture Git directory'}
                $directories[$name]=$true;$pending.Enqueue($entry.FullName);continue
            }
            $encoded=$declaration.files.PSObject.Properties[$name].Value
            if($null -eq $encoded){throw 'Unknown fixture Git file'}
            $bytes=[Convert]::FromBase64String($encoded)
            $hash=[Security.Cryptography.SHA256]::Create()
            try{$digest=([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
            if($entry.Length -ne $bytes.Length -or (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $digest){throw 'Fixture Git bytes differ from declared reconstruction'}
            $actual[$name]=$true
        }
    }
    if($actual.Count -ne @($declaration.files.PSObject.Properties).Count -or $directories.Count -ne @($declaration.directories).Count){throw 'Fixture Git inventory incomplete'}
    Remove-Item -LiteralPath $target -Recurse -Force
    if(Test-Path -LiteralPath $target){throw 'Declared Git fixture metadata remains'}
}
Write-Output 'Removed only exact declared reconstructible empty Git metadata before staging ordinary fixture files.'
