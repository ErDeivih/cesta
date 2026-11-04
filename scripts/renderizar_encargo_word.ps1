param(
    [Parameter(Mandatory=$true)][string]$Documento,
    [Parameter(Mandatory=$true)][string]$SalidaPdf
)
$ErrorActionPreference = 'Stop'
$documentoResuelto = (Resolve-Path -LiteralPath $Documento).Path
$salidaResuelta = [System.IO.Path]::GetFullPath($SalidaPdf)
$wordEncargo = $null
$docEncargo = $null
try {
    $wordEncargo = New-Object -ComObject Word.Application
    $wordEncargo.Visible = $false
    $wordEncargo.DisplayAlerts = 0
    $docEncargo = $wordEncargo.Documents.Open($documentoResuelto, $false, $true, $false)
    $docEncargo.Repaginate()
    $docEncargo.ExportAsFixedFormat($salidaResuelta, 17)
    Write-Output "Renderizado: $salidaResuelta"
} finally {
    if ($null -ne $docEncargo) {
        $docEncargo.Close(0)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($docEncargo)
    }
    if ($null -ne $wordEncargo) {
        # No cerrar otros documentos si Office ha reutilizado una instancia.
        if ($wordEncargo.Documents.Count -eq 0) { $wordEncargo.Quit() }
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordEncargo)
    }
}
