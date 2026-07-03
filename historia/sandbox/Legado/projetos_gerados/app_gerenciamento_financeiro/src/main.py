package app;
import java.util.Scanner;
public class Main {
    private static Scanner scanner = new Scanner(System.in);
    private static BudgetManager budgetManager = new BudgetManager();
    private static InvestmentManager investmentManager = new InvestmentManager();
    public static void main(String[] args) {
        init();
        loopPrincipal();
    }
    private static void init() {
        System.out.println("Inicializando aplicativo de gerenciamento financeiro...");
        // Aqui você pode adicionar qualquer inicialização necessária
        budgetManager.loadBudgets();
        investmentManager.loadInvestments();
        System.out.println("Aplicativo inicializado com sucesso!");
    }
    private static void loopPrincipal() {
        while (true) {
            exibirMenu();
            int opcao = scanner.nextInt();
            scanner.nextLine(); // Limpar buffer
            switch (opcao) {
                case 1:
                    budgetManager.criarOrçamento();
                    break;
                case 2:
                    budgetManager.exibirOrçamentos();
                    break;
                case 3:
                    investmentManager.realizarInvestimento();
                    break;
                case 4:
                    investmentManager.exibirInvestimentos();
                    break;
                case 5:
                    System.out.println("Saindo do aplicativo...");
                    scanner.close();
                    return;
                default:
                    System.out.println("Opção inválida. Tente novamente.");
            }
        }
    }
    private static void exibirMenu() {
        System.out.println("\nMenu Principal:");
        System.out.println("1. Criar Orçamento");
        System.out.println("2. Exibir Orçamentos");
        System.out.println("3. Realizar Investimento");
        System.out.println("4. Exibir Investimentos");
        System.out.println("5. Sair");
        System.out.print("Escolha uma opção: ");
    }
}
class BudgetManager {
    public void criarOrçamento() {
        // Implementação para criar um orçamento
        System.out.println("Criando novo orçamento...");
        // Aqui você pode adicionar a lógica para criar e salvar o orçamento
    }
    public void exibirOrçamentos() {
        // Implementação para exibir orçamentos
        System.out.println("Exibindo orçamentos...");
        // Aqui você pode adicionar a lógica para listar os orçamentos
    }
    public void loadBudgets() {
        // Implementação para carregar orçamentos de um arquivo ou banco de dados
        System.out.println("Carregando orçamentos...");
    }
}
class InvestmentManager {
    public void realizarInvestimento() {
        // Implementação para realizar investimentos
        System.out.println("Realizando investimento...");
        // Aqui você pode adicionar a lógica para realizar e salvar o investimento
    }
    public void exibirInvestimentos() {
        // Implementação para exibir investimentos
        System.out.println("Exibindo investimentos...");
        // Aqui você pode adicionar a lógica para listar os investimentos
    }
    public void loadInvestments() {
        // Implementação para carregar investimentos de um arquivo ou banco de dados
        System.out.println("Carregando investimentos...");
    }
}
### Explicação do Código:
1. **Main Class**:
   - O ponto de entrada do aplicativo (`main` method).
   - Inicializa o aplicativo com a função `init`.
   - Executa um loop principal que exibe um menu e processa as opções selecionadas pelo usuário.
2. **BudgetManager Class**:
   - Gerencia os orçamentos.
   - Fornece métodos para criar, exibir e carregar orçamentos.
3. **InvestmentManager Class**:
   - Gerencia os investimentos.
   - Fornece métodos para realizar, exibir e carregar investimentos.
### Notas:
- Este código é um exemplo básico e pode ser expandido com funcionalidades adicionais como salvar dados em arquivos ou bancos de dados, validações mais robustas, etc.
- O `Scanner` é usado para capturar a entrada do usuário. Dependendo da plataforma mobile, você pode precisar usar uma biblioteca específica para lidar com a interface do usuário.
- As funções `loadBudgets` e `loadInvestments` são placeholders que você deve implementar de acordo com sua necessidade (por exemplo, carregar dados de um arquivo ou banco de dados).