#!/usr/bin/env bash
# ==============================================================================
# Script d'exécution automatisée des tests unitaires (Python & C#)
# R5.A.7 - Mise en pratique conteneurisation (Jalon J7)
# ==============================================================================

set -e

echo ""
echo "======================================================="
echo " [Projet_QRcode] Lancement de la suite de Tests Unitaires"
echo "======================================================="
echo ""

# 1. Tests Python
echo "-------------------------------------------------------"
echo " [1/2] Tests Unitaires Python (Job-Python & Ambassadeur)"
echo "-------------------------------------------------------"

if command -v pytest &> /dev/null; then
    pytest tests -v
else
    python3 -m unittest discover -s tests -p "test_*.py" -v 2>/dev/null || python -m unittest discover -s tests -p "test_*.py" -v
fi

echo ""
echo "✅ Succès : Tous les tests unitaires Python sont passés avec succès."
echo ""

# 2. Tests C# .NET
echo "-------------------------------------------------------"
echo " [2/2] Tests Unitaires C# .NET (DataService.Tests)"
echo "-------------------------------------------------------"

dotnet test data-csharp.Tests/data-csharp.Tests.csproj --verbosity normal

echo ""
echo "✅ Succès : Tous les tests unitaires C# sont passés avec succès."
echo ""

echo "======================================================="
echo " 🎉 Tous les tests unitaires du projet ont réussi !"
echo "======================================================="
echo ""
