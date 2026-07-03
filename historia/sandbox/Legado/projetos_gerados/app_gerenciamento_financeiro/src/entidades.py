package app;
import java.util.ArrayList;
import java.util.List;
public class Entidades {
    // Classe para representar uma transação financeira
    public static class Transacao {
        private String descricao;
        private double valor;
        private String categoria;
        private boolean ehReceita;
        public Transacao(String descricao, double valor, String categoria, boolean ehReceita) {
            this.descricao = descricao;
            this.valor = valor;
            this.categoria = categoria;
            this.ehReceita = ehReceita;
        }
        public String getDescricao() {
            return descricao;
        }
        public void setDescricao(String descricao) {
            this.descricao = descricao;
        }
        public double getValor() {
            return valor;
        }
        public void setValor(double valor) {
            this.valor = valor;
        }
        public String getCategoria() {
            return categoria;
        }
        public void setCategoria(String categoria) {
            this.categoria = categoria;
        }
        public boolean isEhReceita() {
            return ehReceita;
        }
        public void setEhReceita(boolean ehReceita) {
            this.ehReceita = ehReceita;
        }
    }
    // Classe para representar um orçamento
    public static class Orcamento {
        private double valorTotal;
        private List<Transacao> transacoes;
        public Orcamento(double valorTotal) {
            this.valorTotal = valorTotal;
            this.transacoes = new ArrayList<>();
        }
        public double getValorTotal() {
            return valorTotal;
        }
        public void setValorTotal(double valorTotal) {
            this.valorTotal = valorTotal;
        }
        public List<Transacao> getTransacoes() {
            return transacoes;
        }
        public void addTransacao(Transacao transacao) {
            this.transacoes.add(transacao);
        }
        public double calcularSaldo() {
            double saldo = 0;
            for (Transacao t : transacoes) {
                if (t.isEhReceita()) {
                    saldo += t.getValor();
                } else {
                    saldo -= t.getValor();
                }
            }
            return saldo;
        }
    }
    // Classe para representar um investimento
    public static class Investimento {
        private String nome;
        private double valorInvestido;
        private double rentabilidade;
        public Investimento(String nome, double valorInvestido, double rentabilidade) {
            this.nome = nome;
            this.valorInvestido = valorInvestido;
            this.rentabilidade = rentabilidade;
        }
        public String getNome() {
            return nome;
        }
        public void setNome(String nome) {
            this.nome = nome;
        }
        public double getValorInvestido() {
            return valorInvestido;
        }
        public void setValorInvestido(double valorInvestido) {
            this.valorInvestido = valorInvestido;
        }
        public double getRentabilidade() {
            return rentabilidade;
        }
        public void setRentabilidade(double rentabilidade) {
            this.rentabilidade = rentabilidade;
        }
        public double calcularLucro() {
            return valorInvestido * (rentabilidade / 100);
        }
    }
    // Classe para representar um usuário
    public static class Usuario {
        private String nome;
        private List<Orcamento> orcamentos;
        private List<Investimento> investimentos;
        public Usuario(String nome) {
            this.nome = nome;
            this.orcamentos = new ArrayList<>();
            this.investimentos = new ArrayList<>();
        }
        public String getNome() {
            return nome;
        }
        public void setNome(String nome) {
            this.nome = nome;
        }
        public List<Orcamento> getOrcamentos() {
            return orcamentos;
        }
        public void addOrcamento(Orcamento orcamento) {
            this.orcamentos.add(orcamento);
        }
        public List<Investimento> getInvestimentos() {
            return investimentos;
        }
        public void addInvestimento(Investimento investimento) {
            this.investimentos.add(investimento);
        }
    }
}
Este código define as seguintes classes:
1. `Transacao`: Representa uma transação financeira, com descrição, valor, categoria e se é receita ou despesa.
2. `Orcamento`: Representa um orçamento, com um valor total e uma lista de transações. Inclui um método para calcular o saldo do orçamento.
3. `Investimento`: Representa um investimento, com nome, valor investido e rentabilidade. Inclui um método para calcular o lucro do investimento.
4. `Usuario`: Representa um usuário, com nome, lista de orçamentos e lista de investimentos.
Este módulo pode ser usado como base para implementar as funcionalidades de gerenciamento financeiro em seu aplicativo mobile.