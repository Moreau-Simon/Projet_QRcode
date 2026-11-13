using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Npgsql;
using StackExchange.Redis;

var builder = WebApplication.CreateBuilder(args);

// 1. Configuration Redis dynamique via variables d'environnement
var redisHost = Environment.GetEnvironmentVariable("REDIS_HOST") ?? "redis";
var redisPort = Environment.GetEnvironmentVariable("REDIS_PORT") ?? "6379";
var redisConfig = ConfigurationOptions.Parse($"{redisHost}:{redisPort}");
redisConfig.AbortOnConnectFail = false; // Ne crashe pas si Redis met quelques secondes à démarrer
var redis = ConnectionMultiplexer.Connect(redisConfig);
builder.Services.AddSingleton<IConnectionMultiplexer>(redis);

// 2. Configuration PostgreSQL dynamique via variables d'environnement (utilisateur dédié non-root)
var psqlHost = Environment.GetEnvironmentVariable("PSQL_HOST") ?? "psql";
var psqlPort = Environment.GetEnvironmentVariable("PSQL_PORT") ?? "5432";
var psqlDb = Environment.GetEnvironmentVariable("POSTGRES_DB") ?? "ma_base_de_donnees";
var psqlUser = Environment.GetEnvironmentVariable("APP_DB_USER") ?? "data_user";
var psqlPass = Environment.GetEnvironmentVariable("APP_DB_PASSWORD") ?? "data_secure_password";

var pgConnString = Environment.GetEnvironmentVariable("CONNECTION_STRING")
    ?? $"Host={psqlHost};Port={psqlPort};Username={psqlUser};Password={psqlPass};Database={psqlDb}";
builder.Services.AddScoped(_ => new NpgsqlConnection(pgConnString));

// 3. Configuration Swagger / OpenAPI (Jalon J2)
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "DataService API",
        Version = "v1",
        Description = "Microservice Data Access C# pour la gestion des QR-Codes et codes-barres (PostgreSQL & Redis)"
    });
});

var app = builder.Build();

// Activation de Swagger et de son interface interactive
app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "DataService API v1");
    c.RoutePrefix = "swagger";
});

// 4. Initialisation de la base de données (Vérification / création de la table si nécessaire)
try
{
    using var scope = app.Services.CreateScope();
    var conn = scope.ServiceProvider.GetRequiredService<NpgsqlConnection>();
    conn.Open();
    using var cmd = new NpgsqlCommand(@"
        CREATE TABLE IF NOT EXISTS scans (
            id SERIAL PRIMARY KEY,
            barcode_data VARCHAR(255) UNIQUE NOT NULL,
            scan_count INT DEFAULT 1,
            last_scan TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )", conn);
    cmd.ExecuteNonQuery();
}
catch (Exception ex)
{
    Console.WriteLine($"[AVERTISSEMENT] Initialisation table : {ex.Message}");
}

// 5. Endpoint appelé par l'Ambassadeur Python : enregistre CHAQUE scan
app.MapPost("/api/save", async (ScanRequest req, IConnectionMultiplexer redisClient, NpgsqlConnection pgConn) =>
{
    if (string.IsNullOrWhiteSpace(req.Valeur))
    {
        return Results.BadRequest(new { status = "error", message = "La valeur du scan ne peut être vide." });
    }

    var db = redisClient.GetDatabase();
    var cacheKey = $"barcode:{req.Valeur}";

    // A. Insérer ou mettre à jour dans PostgreSQL (compteur + date du dernier scan)
    await pgConn.OpenAsync();
    using var cmd = new NpgsqlCommand(@"
        INSERT INTO scans (barcode_data) VALUES (@val)
        ON CONFLICT (barcode_data) DO UPDATE SET
            scan_count = scans.scan_count + 1,
            last_scan = CURRENT_TIMESTAMP
        RETURNING scan_count;", pgConn);
    cmd.Parameters.AddWithValue("val", req.Valeur);

    var count = Convert.ToInt32(await cmd.ExecuteScalarAsync());

    // B. Mettre à jour le cache Redis avec le compteur actuel (expire après 1 heure)
    await db.StringSetAsync(cacheKey, count, TimeSpan.FromHours(1));

    return Results.Ok(new { status = "success", source = "postgres", data = req.Valeur, scan_count = count });
})
.WithName("SaveScan")
.WithSummary("Enregistre un code scanné dans PostgreSQL et met à jour le cache Redis.")
.Produces(StatusCodes.Status200OK)
.Produces(StatusCodes.Status400BadRequest);

// 6. Consultation d'un code : lecture dans Redis d'abord, sinon PostgreSQL
app.MapGet("/api/scan/{valeur}", async (string valeur, IConnectionMultiplexer redisClient, NpgsqlConnection pgConn) =>
{
    if (string.IsNullOrWhiteSpace(valeur))
    {
        return Results.BadRequest(new { status = "error", message = "Le paramètre valeur est obligatoire." });
    }

    var db = redisClient.GetDatabase();
    var cacheKey = $"barcode:{valeur}";

    var cached = await db.StringGetAsync(cacheKey);
    if (!cached.IsNull)
    {
        return Results.Ok(new { status = "success", source = "redis", data = valeur, scan_count = (int)cached });
    }

    await pgConn.OpenAsync();
    using var cmd = new NpgsqlCommand("SELECT scan_count FROM scans WHERE barcode_data = @val", pgConn);
    cmd.Parameters.AddWithValue("val", valeur);
    var result = await cmd.ExecuteScalarAsync();

    if (result is null)
    {
        return Results.NotFound(new { status = "error", message = "Code inconnu." });
    }

    var count = Convert.ToInt32(result);
    await db.StringSetAsync(cacheKey, count, TimeSpan.FromHours(1));
    return Results.Ok(new { status = "success", source = "postgres", data = valeur, scan_count = count });
})
.WithName("GetScan")
.WithSummary("Consulte les informations d'un code (stratégie Cache-Aside : Redis puis PostgreSQL).")
.Produces(StatusCodes.Status200OK)
.Produces(StatusCodes.Status404NotFound)
.Produces(StatusCodes.Status400BadRequest);

// L'API écoute sur le port 5000
app.Run("http://0.0.0.0:5000");

public class ScanRequest
{
    public string Valeur { get; set; } = string.Empty;
}

public partial class Program { }
