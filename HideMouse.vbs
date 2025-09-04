' mouse_hider.vbs
Option Explicit
Dim WShell, FSO, LogFile, TempFolder, BlankCursorPath
Set WShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
TempFolder = "C:\Temp"
BlankCursorPath = TempFolder & "\blank.cur"

' Create Temp folder if it doesn't exist
If Not FSO.FolderExists(TempFolder) Then
    FSO.CreateFolder(TempFolder)
End If

' Create log file
Set LogFile = FSO.CreateTextFile(TempFolder & "\screenconnect_mouse_hider.log", True)
LogFile.WriteLine Now & " [INFO] Starting mouse hider script"

' Create blank cursor file
On Error Resume Next
Dim BlankCursor
Set BlankCursor = FSO.CreateTextFile(BlankCursorPath, True)
BlankCursor.Write Chr(0) & Chr(0) & Chr(1) & Chr(0) & Chr(1) & Chr(0) & Chr(1) & Chr(1) & _
    Chr(0) & Chr(0) & Chr(1) & Chr(0) & Chr(32) & Chr(0) & Chr(16) & Chr(0) & _
    String(28, Chr(0))
BlankCursor.Close
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Created blank cursor at " & BlankCursorPath
Else
    LogFile.WriteLine Now & " [ERROR] Failed to create blank cursor: " & Err.Description
End If
On Error GoTo 0

' Set blank cursor
On Error Resume Next
WShell.RegWrite "HKCU\Control Panel\Cursors\Arrow", BlankCursorPath, "REG_SZ"
WShell.Run "rundll32.exe user32.dll, SystemParametersInfo 0x0057 0 """ & BlankCursorPath & """ 0", 0, True
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Set blank cursor"
Else
    LogFile.WriteLine Now & " [ERROR] Failed to set blank cursor: " & Err.Description
End If
On Error GoTo 0

' Wait for 5 minutes (session duration)
WScript.Sleep 300000

' Restore default cursor
On Error Resume Next
WShell.RegWrite "HKCU\Control Panel\Cursors\Arrow", "", "REG_SZ"
WShell.Run "rundll32.exe user32.dll, SystemParametersInfo 0x0057 0 """" 0", 0, True
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Restored default cursor"
Else
    LogFile.WriteLine Now & " [ERROR] Failed to restore default cursor: " & Err.Description
End If
On Error GoTo 0

' Close log file
LogFile.Close
