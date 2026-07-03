package app;
import java.text.DecimalFormat;
import java.util.Locale;
public class Utils {
    // Formata uma quantidade monetária para o formato local (por exemplo, USD, BRL)
    public static String formatCurrency(double amount) {
        Locale locale = new Locale("pt", "BR"); // Brasil
        DecimalFormat decimalFormat = (DecimalFormat) DecimalFormat.getCurrencyInstance(locale);
        return decimalFormat.format(amount);
    }
    // Converte uma string em formato monetário para um double
    public static double parseCurrency(String currencyString) {
        try {
            Locale locale = new Locale("pt", "BR"); // Brasil
            Number number = DecimalFormat.getCurrencyInstance(locale).parse(currencyString);
            return number.doubleValue();
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid currency format: " + currencyString, e);
        }
    }
    // Verifica se um valor é válido para orçamento ou investimento
    public static boolean isValidAmount(double amount) {
        return amount > 0;
    }
    // Gera uma string aleatória de caracteres alfanuméricos com o tamanho especificado
    public static String generateRandomString(int length) {
        StringBuilder sb = new StringBuilder();
        String characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        for (int i = 0; i < length; i++) {
            int index = (int) (Math.random() * characters.length());
            sb.append(characters.charAt(index));
        }
        return sb.toString();
    }
    // Converte um valor em porcentagem para decimal
    public static double convertPercentageToDecimal(double percentage) {
        return percentage / 100;
    }
    // Converte um valor em decimal para porcentagem
    public static double convertDecimalToPercentage(double decimal) {
        return decimal * 100;
    }
}
Este módulo `Utils.java` fornece várias funções utilitárias que podem ser úteis para o desenvolvimento de um aplicativo mobile de gerenciamento financeiro. As principais funcionalidades incluem:
1. **Formatação de moeda**: Converte valores numéricos em strings formatadas como moeda local.
2. **Parsing de moeda**: Converte strings formatadas como moeda de volta para valores numéricos.
3. **Validação de valor**: Verifica se um valor é válido (maior que zero) para orçamento ou investimento.
4. **Geração de string aleatória**: Cria uma string aleatória de caracteres alfanuméricos, útil para gerar IDs únicos.
5. **Conversão entre porcentagem e decimal**: Auxilia na manipulação de taxas de juros ou retornos de investimentos.
Você pode adaptar este código conforme necessário para atender às especificidades do seu aplicativo.