# Holds the system awake (prevents sleep) while the parent process (the
# run-pipeline.bat cmd instance) is running. Launched via:
#   start "" /b powershell -NoProfile -ExecutionPolicy Bypass -File scripts\keep_awake.ps1
# ES_CONTINUOUS is auto-cleared by Windows when this process exits, so there is
# no way for this to leave the machine permanently insomniac.
Add-Type -Name Power -Namespace Win32 -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
$ES_CONTINUOUS = [uint32]"0x80000000"
$ES_SYSTEM_REQUIRED = [uint32]"0x00000001"
[Win32.Power]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED) | Out-Null
$parent = (Get-CimInstance Win32_Process -Filter "ProcessId=$PID").ParentProcessId
try {
    Wait-Process -Id $parent -ErrorAction SilentlyContinue
} finally {
    [Win32.Power]::SetThreadExecutionState($ES_CONTINUOUS) | Out-Null
}
