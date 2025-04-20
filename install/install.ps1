# Get the script directory path regardless of how the script is invoked
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath
$repoRoot = Split-Path -Parent $scriptDir

# Defined versions of Python and CUDA
$requiredPythonVersion = "3.12"
$requiredCudaVersion = "12.6"

# Display help information
function Show-Help {
    Write-Host "Python Environment Setup Script" -ForegroundColor Cyan
    Write-Host "============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This script creates Python virtual environments for different usage scenarios."
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\install.ps1 [mode] [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Modes:" -ForegroundColor Green
    Write-Host "  app        Creates a lightweight application environment (.venv)"
    Write-Host "  dev        Creates a development environment with PyTorch CPU (.venv_dev)"
    Write-Host "  dev_cuda   Creates a development environment with PyTorch CUDA (.venv_dev)"
    Write-Host "  help       Displays this help information"
    Write-Host ""
    Write-Host "If no mode is specified, 'app' is used by default."
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -force     Recreate the environment without asking for confirmation"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\install.ps1                   # Create application environment"
    Write-Host "  .\install.ps1 app               # Create application environment"
    Write-Host "  .\install.ps1 dev               # Create development environment with PyTorch CPU"
    Write-Host "  .\install.ps1 dev_cuda          # Create development environment with PyTorch CUDA"
    Write-Host "  .\install.ps1 dev_cuda -force   # Force recreation of dev CUDA environment"
    Write-Host ""
}

# Function to find specific Python version
function Find-PythonVersion {
    param (
        [string]$version
    )

    $pythonCommands = @("python", "python3", "py -$version", "python$version", "python3.$version")
    $pythonPaths = @(
        # Common Windows paths
        "C:\Python$version\python.exe",
        "${env:LOCALAPPDATA}\Programs\Python\Python$($version.Replace('.',''))\python.exe",
        "${env:ProgramFiles}\Python$($version.Replace('.',''))\python.exe",
        "${env:ProgramFiles(x86)}\Python$($version.Replace('.',''))\python.exe"
    )

    # First try commands that might be in PATH
    foreach ($cmd in $pythonCommands) {
        try {
            $output = Invoke-Expression "$cmd -c `"import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')`""
            if ($output -like "$version*") {
                Write-Host "Found Python $version using command: $cmd" -ForegroundColor Green
                return $cmd
            }
        } catch {
            # Command failed, try next one
        }
    }

    # Then try specific file paths
    foreach ($path in $pythonPaths) {
        if (Test-Path $path) {
            try {
                $output = & $path -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
                if ($output -like "$version*") {
                    Write-Host "Found Python $version at: $path" -ForegroundColor Green
                    return $path
                }
            } catch {
                # Command failed, try next one
            }
        }
    }

    # Try the py launcher with version specification (Windows)
    try {
        $pyLauncherOutput = py -0
        if ($pyLauncherOutput -match "$version") {
            Write-Host "Python $version available through py launcher" -ForegroundColor Green
            return "py -$version"
        }
    } catch {
        # py launcher not available or failed
    }

    # No Python found with requested version
    return $null
}

# Function to check for CUDA availability
function Check-CudaAvailability {
    # Check for NVIDIA GPU and drivers
    try {
        $gpuInfo = Get-WmiObject -Class Win32_VideoController | Where-Object { $_.Name -match "NVIDIA" }
        if ($gpuInfo) {
            # Try to run nvidia-smi
            $nvidiaSmi = & nvidia-smi 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "CUDA-capable GPU detected with drivers installed." -ForegroundColor Green
                return $true
            }
        }
    } catch {
        # WMI query failed or nvidia-smi not available
    }

    Write-Host "CUDA-capable GPU not detected or drivers not installed." -ForegroundColor Yellow
    return $false
}

# Function to create and set up a virtual environment
function Create-VirtualEnv {
    param (
        [string]$pythonCmd,
        [string]$envPath,
        [bool]$installDev = $false,
        [bool]$useCuda = $false,
        [bool]$force = $false
    )

    Write-Host "Creating virtual environment at: $envPath" -ForegroundColor Cyan

    # Check if venv already exists
    if (Test-Path -Path $envPath) {
        if (-not $force) {
            Write-Host "Virtual environment already exists at $envPath. Do you want to recreate it? (y/n)" -ForegroundColor Yellow
            $response = Read-Host
            if ($response -ne 'y') {
                Write-Host "Keeping existing virtual environment." -ForegroundColor Cyan
                return
            }
        } else {
            Write-Host "Force flag set. Recreating existing environment." -ForegroundColor Yellow
        }
        Remove-Item -Path $envPath -Recurse -Force
    }

    # Create the virtual environment
    if ($pythonCmd -like "py *") {
        Invoke-Expression "$pythonCmd -m venv $envPath"
    } else {
        & $pythonCmd -m venv $envPath
    }

    if (-not (Test-Path -Path $envPath)) {
        Write-Host "Failed to create virtual environment!" -ForegroundColor Red
        return
    }

    Write-Host "Virtual environment created successfully!" -ForegroundColor Green

    # Determine python path in the virtual environment
    $pythonPath = Join-Path -Path $envPath -ChildPath "Scripts\python.exe"
    if (-not (Test-Path $pythonPath)) {
        Write-Host "Failed to find python in created environment!" -ForegroundColor Red
        return
    }

    # Upgrade pip using the Python executable
    Write-Host "Upgrading pip..." -ForegroundColor Cyan
    & $pythonPath -m pip install --upgrade pip

    # Install requirements
    Write-Host "Installing packages from requirements files..." -ForegroundColor Cyan

    Write-Host "Installing core packages" -ForegroundColor Cyan
    & $pythonPath -m pip install -r "$scriptDir/req_core.txt"

    if ($installDev) {
        Write-Host "Installing dev packages" -ForegroundColor Cyan
        & $pythonPath -m pip install -r "$scriptDir/req_dev.txt"
    }
    if ($installDev -and $useCuda) {
        Write-Host "Installing PyTorch CUDA" -ForegroundColor Green
        & $pythonPath -m pip install -r "$scriptDir/req_pytorch.txt" --index-url "https://download.pytorch.org/whl/cu$($requiredCudaVersion.Replace('.',''))"
    }
    if ($installDev -and -not $useCuda) {
        Write-Host "Installing PyTorch CPU" -ForegroundColor Green
        & $pythonPath -m pip install -r "$scriptDir/req_pytorch.txt"
    }

    Write-Host "`nVirtual environment setup complete!" -ForegroundColor Green
}

# Main script starts here

# Default parameters
$mode = "app"
$force = $false

# Parse command line arguments
for ($i = 0; $i -lt $args.Count; $i++) {
    $arg = $args[$i].ToLower()
    if ($arg -eq "app" -or $arg -eq "dev" -or $arg -eq "dev_cuda" -or $arg -eq "help") {
        $mode = $arg
    } elseif ($arg -eq "-force" -or $arg -eq "-f") {
        $force = $true
    } elseif ($arg -eq "-help" -or $arg -eq "--help" -or $arg -eq "-h" -or $arg -eq "/?") {
        $mode = "help"
    }
}

# Display help if requested
if ($mode -eq "help") {
    Show-Help
    exit 0
}

# Find Python
$python = Find-PythonVersion $requiredPythonVersion

if (-not $python) {
    Write-Host "Python $requiredPythonVersion not found on your system." -ForegroundColor Red
    Write-Host "Please install Python $requiredPythonVersion from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "After installation, ensure it's added to your PATH." -ForegroundColor Yellow
    exit 1
}

# Set up the appropriate environment based on mode
if ($mode -eq "app") {
    $envPath = Join-Path -Path $repoRoot -ChildPath ".venv"

    Write-Host "Setting up application environment (.venv)" -ForegroundColor Cyan
    Create-VirtualEnv -pythonCmd $python -envPath $envPath -force $force

} elseif ($mode -eq "dev" -or $mode -eq "dev_cuda") {
    $envPath = Join-Path -Path $repoRoot -ChildPath ".venv_dev"

    # Check if user explicitly requested CUDA
    $useCuda = $mode -eq "dev_cuda"

    # If CUDA was requested, verify it's available
    if ($useCuda) {
        $cudaAvailable = Check-CudaAvailability
        if (-not $cudaAvailable) {
            Write-Host "Warning: CUDA support was requested but no CUDA-capable GPU was detected." -ForegroundColor Yellow
            Write-Host "The script will still attempt to install PyTorch with CUDA support, but it may not work properly." -ForegroundColor Yellow
            Write-Host "Press Enter to continue or Ctrl+C to abort..." -ForegroundColor Yellow
            Read-Host
        }
    }

    Write-Host "Setting up development environment (.venv_dev)" -ForegroundColor Cyan
    if ($useCuda) {
        Write-Host "PyTorch will be installed with CUDA support" -ForegroundColor Cyan
    } else {
        Write-Host "PyTorch will be installed without CUDA support (CPU only)" -ForegroundColor Cyan
    }

    Create-VirtualEnv -pythonCmd $python -envPath $envPath -installDev $true -useCuda $useCuda -force $force

} else {
    Write-Host "Invalid mode: $mode" -ForegroundColor Red
    Write-Host "Use 'help' mode to see available options" -ForegroundColor Yellow
    exit 1
}
