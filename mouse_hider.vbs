' mouse_hider.vbs
Option Explicit
Dim WShell, FSO, LogFile, TempFolder, BlankCursorPath
Set WShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
TempFolder = "C:\Temp"
BlankCursorPath = TempFolder & "\blank.cur"

' Create Temp folder if it doesn't exist
On Error Resume Next
If Not FSO.FolderExists(TempFolder) Then
    FSO.CreateFolder(TempFolder)
    If Err.Number = 0 Then
        LogFile.WriteLine Now & " [INFO] Created Temp folder at " & TempFolder
    Else
        WScript.Echo "Failed to create Temp folder: " & Err.Description
        WScript.Quit
    End If
End If

' Create log file
Set LogFile = FSO.CreateTextFile(TempFolder & "\screenconnect_mouse_hider.log", True)
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Starting mouse hider script"
Else
    WScript.Echo "Failed to create log file: " & Err.Description
    WScript.Quit
End If
Err.Clear
On Error GoTo 0

' Create blank cursor file
On Error Resume Next
Dim BlankCursor
Set BlankCursor = FSO.CreateTextFile(BlankCursorPath, True)
' Write valid .cur file binary data (1x1 transparent cursor)
BlankCursor.Write Chr(0) & Chr(0) & Chr(2) & Chr(0) & Chr(1) & Chr(0) & Chr(1) & Chr(1) & _
    Chr(0) & Chr(0) & Chr(1) & Chr(0) & Chr(32) & Chr(0) & Chr(16) & Chr(0) & _
    Chr(0) & Chr(0) & Chr(0) & Chr(0) & Chr(0) & Chr(0) & Chr(0) & Chr(0) & _
    Chr(1) & Chr(0) & Chr(0) & Chr(0) & Chr(0) & Chr(0) & Chr(0) & Chr(0) & _
    Chr(255) & Chr(255) & Chr(255) & Chr(255) & Chr(0) & Chr(0) & Chr(0) & Chr(0)
BlankCursor.Close
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Created blank cursor at " & BlankCursorPath
Else
    LogFile.WriteLine Now & " [ERROR] Failed to create blank cursor: " & Err.Description
    LogFile.Close
    WScript.Quit
End If
Err.Clear
On Error GoTo 0

' Verify blank cursor file exists
If Not FSO.FileExists(BlankCursorPath) Then
    LogFile.WriteLine Now & " [ERROR] Blank cursor file not found at " & BlankCursorPath
    LogFile.Close
    WScript.Quit
End If
LogFile.WriteLine Now & " [INFO] Verified blank cursor at " & BlankCursorPath

' Set blank cursor using PowerShell
On Error Resume Next
Dim PsCommand
PsCommand = "powershell -ExecutionPolicy Bypass -Command ""$cursorPath = '" & BlankCursorPath & "'; if (Test-Path $cursorPath) { Set-ItemProperty -Path 'HKCU:\Control Panel\Cursors' -Name 'Arrow' -Value $cursorPath; Add-Type -Name User32 -Namespace Win32 -MemberDefinition '[DllImport(""user32.dll"")] public static extern bool SystemParametersInfo(int uiAction, int uiParam, string pvParam, int fWinIni);'; [Win32.User32]::SystemParametersInfo(0x0057, 0, $cursorPath, 0); Write-Output 'Cursor set' } else { Write-Error 'Blank cursor file not found' }"""
WShell.Run PsCommand, 0, True
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Mouse cursor hidden using blank cursor"
Else
    LogFile.WriteLine Now & " [ERROR] Failed to hide mouse cursor: " & Err.Description
End If
Err.Clear

' Wait for 5 minutes (300,000 milliseconds)
WScript.Sleep 300000

' Restore default cursor
PsCommand = "powershell -ExecutionPolicy Bypass -Command ""Set-ItemProperty -Path 'HKCU:\Control Panel\Cursors' -Name 'Arrow' -Value ''; Add-Type -Name User32 -Namespace Win32 -MemberDefinition '[DllImport(""user32.dll"")] public static extern bool SystemParametersInfo(int uiAction, int uiParam, string pvParam, int fWinIni);'; [Win32.User32]::SystemParametersInfo(0x0057, 0, '', 0); Write-Output 'Cursor restored'"""
WShell.Run PsCommand, 0, True
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Restored default cursor"
Else
    LogFile.WriteLine Now & " [ERROR] Failed to restore default cursor: " & Err.Description
End If
Err.Clear
On Error GoTo 0

' Close log file
LogFile.Close
