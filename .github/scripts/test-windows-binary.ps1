# test_gui_program.ps1

param (
    [Parameter(Mandatory = $true)]
    [string]$ProgramPath
    [Parameter(Mandatory = $true)]
    [string]$GithubToken
    [Parameter(Mandatory = $true)]
    [string]$GithubUser
)

# Start the GUI program in the background
$process = Start-Process -FilePath $ProgramPath -ArgumentList "github_token=$GithubToken", "github_user=$GithubUser" -PassThru
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
