package com.app;
import java.util.ArrayList;
import java.util.List;
public class Fases {
    private List<Fase> fases;
    public Fases() {
        this.fases = new ArrayList<>();
        inicializarFases();
    }
    private void inicializarFases() {
        // Fase 1: Criar Orçamento
        Fase fase1 = new Fase("Criar Orçamento", "Crie seu orçamento mensal.");
        fase1.adicionarRequisito(new Requisito("Definir renda total"));
        fase1.adicionarRequisito(new Requisito("Listar despesas fixas"));
        fase1.adicionarRequisito(new Requisito("Listar despesas variáveis"));
        fases.add(fase1);
        // Fase 2: Gerenciar Investimentos
        Fase fase2 = new Fase("Gerenciar Investimentos", "Adicione seus investimentos.");
        fase2.adicionarRequisito(new Requisito("Definir metas de investimento"));
        fase2.adicionarRequisito(new Requisito("Escolher tipos de investimentos"));
        fases.add(fase2);
        // Fase 3: Monitorar Orçamento
        Fase fase3 = new Fase("Monitorar Orçamento", "Monitore seu orçamento.");
        fase3.adicionarRequisito(new Requisito("Visualizar despesas totais"));
        fase3.adicionarRequisito(new Requisito("Comparar com orçamento"));
        fases.add(fase3);
        // Fase 4: Ajustes e Otimizações
        Fase fase4 = new Fase("Ajustes e Otimizações", "Faça ajustes para otimizar seu gerenciamento financeiro.");
        fase4.adicionarRequisito(new Requisito("Realizar ajustes no orçamento"));
        fase4.adicionarRequisito(new Requisito("Optimizar investimentos"));
        fases.add(fase4);
    }
    public List<Fase> getFases() {
        return fases;
    }
    public static void main(String[] args) {
        Fases fases = new Fases();
        for (Fase fase : fases.getFases()) {
            System.out.println("Fase: " + fase.getNome());
            System.out.println("Descrição: " + fase.getDescricao());
            System.out.println("Requisitos:");
            for (Requisito requisito : fase.getRequisitos()) {
                System.out.println("- " + requisito.getDescricao());
            }
            System.out.println();
        }
    }
}
class Fase {
    private String nome;
    private String descricao;
    private List<Requisito> requisitos;
    public Fase(String nome, String descricao) {
        this.nome = nome;
        this.descricao = descricao;
        this.requisitos = new ArrayList<>();
    }
    public void adicionarRequisito(Requisito requisito) {
        requisitos.add(requisito);
    }
    public String getNome() {
        return nome;
    }
    public String getDescricao() {
        return descricao;
    }
    public List<Requisito> getRequisitos() {
        return requisitos;
    }
}
class Requisito {
    private String descricao;
    public Requisito(String descricao) {
        this.descricao = descricao;
    }
    public String getDescricao() {
        return descricao;
    }
}
Este código define uma classe `Fases` que contém várias fases do jogo, cada uma com requisitos específicos. As classes `Fase` e `Requisito` são usadas para representar as fases e seus requisitos, respectivamente.
O método `inicializarFases()` cria as fases iniciais do aplicativo, que incluem criar orçamento, gerenciar investimentos, monitorar orçamento e fazer ajustes e otimizações. Cada fase tem uma descrição e uma lista de requisitos associados.
O método `main()` imprime todas as fases e seus requisitos no console para fins de demonstração.