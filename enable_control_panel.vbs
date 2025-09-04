' enable_control_panel.vbs
Option Explicit
Dim WShell, FSO, LogFile, TempFolder
Set WShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
TempFolder = "C:\Temp"

' Create Temp folder if it doesn't exist
If Not FSO.FolderExists(TempFolder) Then
    FSO.CreateFolder(TempFolder)
End If

' Create log file
Set LogFile = FSO.CreateTextFile(TempFolder & "\screenconnect_control_panel.log", True)
LogFile.WriteLine Now & " [INFO] Starting Control Panel enable script"

' Enable Control Panel by removing registry restrictions
On Error Resume Next
' Remove NoControlPanel restriction
WShell.RegDelete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\NoControlPanel"
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Removed NoControlPanel registry key"
ElseIf Err.Number = -2147024891 Then ' Key doesn't exist
    LogFile.WriteLine Now & " [INFO] NoControlPanel key not found, no action needed"
Else
    LogFile.WriteLine Now & " [ERROR] Failed to remove NoControlPanel key: " & Err.Description
End If
Err.Clear

' Remove DisallowCpl restriction
WShell.RegDelete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\DisallowCpl"
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Removed DisallowCpl registry key"
ElseIf Err.Number = -2147024891 Then ' Key doesn't exist
    LogFile.WriteLine Now & " [INFO] DisallowCpl key not found, no action needed"
Else
    LogFile.WriteLine Now & " [ERROR] Failed to remove DisallowCpl key: " & Err.Description
End If
Err.Clear

' Ensure Explorer policy key exists and is clean
WShell.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\", "", "REG_SZ"
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Ensured Explorer policy key exists"
Else
    LogFile.WriteLine Now & " [ERROR] Failed to write Explorer policy key: " & Err.Description
End If
Err.Clear
On Error GoTo 0

' Verify by opening Control Panel
On Error Resume Next
WShell.Run "control", 1, False
If Err.Number = 0 Then
    LogFile.WriteLine Now & " [INFO] Attempted to open Control Panel to verify"
Else
    LogFile.WriteLine Now & " [ERROR] Failed to open Control Panel: " & Err.Description
End If
On Error GoTo 0

' Close log file
LogFile.Close
