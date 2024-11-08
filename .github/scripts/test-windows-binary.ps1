# test_gui_program.ps1

param (
    [Parameter(Mandatory = $true)]
    [string]$ProgramPath,
    [Parameter(Mandatory = $true)]
    [string]$GithubToken,
    [Parameter(Mandatory = $true)]
    [string]$GithubUser
)

$stdoutLog = "stdout.log"
$stderrLog = "stderr.log"

# Start the GUI program in the background
$process = Start-Process -FilePath $ProgramPath `
                         -ArgumentList "github_token=$GithubToken", "github_user=$GithubUser" `
                         -RedirectStandardOutput $stdoutLog `
                         -RedirectStandardError $stderrLog `
                         -PassThru
$processCrashed = $false

# Wait for 60 seconds
Start-Sleep -Seconds 60

# Check if the process is still running
if ($process.HasExited -eq $false) {
    Write-Host "Program is still running after 60 seconds. Terminating..."
    $process.Kill()
    $process.WaitForExit()
} else {
    $processCrashed = $true
    Write-Host "Program exited before 60 seconds."
}

if (Test-Path $stdoutLog) {
    Write-Host "=== Standard Output ==="
    Get-Content $stdoutLog | ForEach-Object { Write-Host $_ }
    Remove-Item $stdoutLog
}

if (Test-Path $stderrLog) {
    Write-Host "=== Standard Error ==="
    Get-Content $stderrLog | ForEach-Object { Write-Host $_ }
    Remove-Item $stderrLog
}

# Get the exit code
$exitCode = $process.ExitCode

# Output the exit code
Write-Host "Exit code: $exitCode"

# Check if the program exited successfully
if ($processCrashed) {
    Write-Host "Program terminated with exit code $exitCode."
    exit $exitCode
} else {
    Write-Host "Program executed successfully."
}
