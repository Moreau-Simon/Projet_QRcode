FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copie le fichier projet et restaure les dépendances (NuGet)
COPY DataService.csproj ./
RUN dotnet restore

# Copie le reste du code et compile
COPY . .
RUN dotnet publish -c Release -o /app/publish

# Image d'exécution allégée
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app/publish .

EXPOSE 5000
ENTRYPOINT ["dotnet", "DataService.dll"]
