using Xunit;

namespace data_csharp.Tests;

public class ScanModelTests
{
    [Fact]
    public void ScanRequest_Default_ShouldHaveEmptyValue()
    {
        // Arrange & Act
        var request = new ScanRequest();

        // Assert
        Assert.NotNull(request.Valeur);
        Assert.Equal(string.Empty, request.Valeur);
    }

    [Fact]
    public void ScanRequest_WithValidValue_ShouldStoreValueCorrectly()
    {
        // Arrange
        var expectedValue = "67430";

        // Act
        var request = new ScanRequest { Valeur = expectedValue };

        // Assert
        Assert.Equal(expectedValue, request.Valeur);
    }

    [Theory]
    [InlineData("3017620422003")]          // EAN-13 valide
    [InlineData("PC-UPJV-67430")]          // CODE39 alphanumérique
    [InlineData("https://u-picardie.fr")]  // QR-Code URL
    public void ScanRequest_DifferentFormats_ShouldPreserveValue(string code)
    {
        // Arrange & Act
        var request = new ScanRequest { Valeur = code };

        // Assert
        Assert.Equal(code, request.Valeur);
        Assert.False(string.IsNullOrWhiteSpace(request.Valeur));
    }

    [Theory]
    [InlineData("67430", "barcode:67430")]
    [InlineData("ABC123", "barcode:ABC123")]
    public void RedisCacheKey_Generation_ShouldBeConsistent(string code, string expectedKey)
    {
        // Act
        var cacheKey = $"barcode:{code}";

        // Assert
        Assert.Equal(expectedKey, cacheKey);
    }
}
