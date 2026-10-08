# Étape 1 : Build
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
# On simule un projet vide pour que le build Docker ne plante pas immédiatement.
# Quand vous aurez créé le vrai projet C# (ex: avec `dotnet new webapi`), 
# cette partie copiera vos vrais fichiers .csproj et .cs
RUN dotnet new console -n DataService -o .
RUN dotnet restore
RUN dotnet publish -c Release -o /app/publish

# Étape 2 : Runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app/publish .
EXPOSE 5000
# Exécute la DLL générée
ENTRYPOINT ["dotnet", "DataService.dll"]
