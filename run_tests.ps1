# ==============================================================================
# Script d'exécution automatisée des tests unitaires (Python & C#)
# R5.A.7 - Mise en pratique conteneurisation (Jalon J7)
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host " [Projet_QRcode] Lancement de la suite de Tests Unitaires" -ForegroundColor Cyan
Write-Host "=======================================================`n" -ForegroundColor Cyan

# 1. Tests Python
Write-Host "-------------------------------------------------------" -ForegroundColor Yellow
Write-Host " [1/2] Tests Unitaires Python (Job-Python & Ambassadeur)" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------" -ForegroundColor Yellow

python -m unittest discover -s tests -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Échec des tests unitaires Python." -ForegroundColor Red
    exit 1
}
Write-Host "`n✅ Succès : Tous les tests unitaires Python sont passés avec succès." -ForegroundColor Green

# 2. Tests C# .NET
Write-Host "`n-------------------------------------------------------" -ForegroundColor Yellow
Write-Host " [2/2] Tests Unitaires C# .NET (DataService.Tests)" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------" -ForegroundColor Yellow

dotnet test data-csharp.Tests/data-csharp.Tests.csproj --verbosity normal
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Échec des tests unitaires C#." -ForegroundColor Red
    exit 1
}
Write-Host "`n✅ Succès : Tous les tests unitaires C# sont passés avec succès." -ForegroundColor Green

Write-Host "`n=======================================================" -ForegroundColor Green
Write-Host " 🎉 Tous les tests unitaires du projet ont réussi !" -ForegroundColor Green
Write-Host "=======================================================`n" -ForegroundColor Green
exit 0
