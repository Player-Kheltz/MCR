"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DocumentController = void 0;
const prisma_1 = require("../lib/prisma");
const zod_1 = require("zod");
const safeJson_1 = require("../lib/safeJson");
const optimizer_1 = require("../lib/optimizer");
const templates = [
    {
        id: 'proposta',
        name: 'Proposta Comercial',
        content: `PROPOSTA COMERCIAL\n\n${'='.repeat(40)}\n\nCliente: {{nome}}\nCPF: {{cpf}}\nTelefone: {{telefone}}\nEmail: {{email}}\nEndereço: {{endereco}}\n\n${'='.repeat(40)}\n\nPrezado(a) {{nome}},\n\nViemos por meio desta apresentar nossa proposta para:\n\n[DESCREVER PROPOSTA]\n\nValor: R$ [VALOR]\nCondições: [CONDIÇÕES]\n\n${'='.repeat(40)}\n\nData: {{data}}\n\n__________________________\nVendedor\n\n__________________________\nCliente`,
    },
    {
        id: 'contrato',
        name: 'Contrato de Venda',
        content: `CONTRATO DE VENDA\n\n${'='.repeat(40)}\n\nPelo presente instrumento particular, de um lado {{nome}}, inscrito(a) sob CPF nº {{cpf}}, residente e domiciliado(a) em {{endereco}}, doravante denominado CONTRATANTE, e de outro lado [NOME DA LOJA], doravante denominada CONTRATADA.\n\nCLÁUSULA 1ª - OBJETO\nO objeto do presente contrato é a venda do produto: [DESCREVER PRODUTO]\n\nCLÁUSULA 2ª - VALOR\nO valor total é de R$ [VALOR], nas seguintes condições: [CONDIÇÕES]\n\nCLÁUSULA 3ª - PRAZO\nO prazo para entrega é de [PRAZO] dias úteis.\n\n${'='.repeat(40)}\n\n{{data}}\n\n__________________________\nVendedor\n\n__________________________\nCliente ({{nome}})`,
    },
    {
        id: 'recibo',
        name: 'Recibo',
        content: `RECIBO\n\n${'='.repeat(40)}\n\nRecebi(emos) de {{nome}}, CPF {{cpf}}, a importância de R$ [VALOR] referente a [DESCRIÇÃO].\n\n${'='.repeat(40)}\n\n{{data}}\n\n__________________________\nAssinatura`,
    },
];
const createSchema = zod_1.z.object({
    templateId: zod_1.z.string().min(1),
    customerId: zod_1.z.string().min(1),
    category: zod_1.z.string().max(50).optional(),
    data: zod_1.z.record(zod_1.z.string(), zod_1.z.any()).optional(),
});
class DocumentController {
    async listTemplates(_req, res) {
        return res.json(templates);
    }
    async list(req, res) {
        try {
            const docs = await prisma_1.prisma.document.findMany({
                where: { customer: { storeId: req.storeId } },
                include: { customer: { select: { id: true, name: true, phone: true } } },
                orderBy: { createdAt: 'desc' },
            });
            return res.json(docs.map(d => ({ ...d, data: (0, safeJson_1.safeJsonParse)(d.data, {}) })));
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao listar documentos' });
        }
    }
    async getById(req, res) {
        try {
            const doc = await prisma_1.prisma.document.findFirst({
                where: { id: req.params.id },
                include: { customer: true },
            });
            if (!doc || doc.customer.storeId !== req.storeId) {
                return res.status(404).json({ error: 'Documento não encontrado' });
            }
            return res.json({ ...doc, data: (0, safeJson_1.safeJsonParse)(doc.data, {}) });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao buscar documento' });
        }
    }
    async create(req, res) {
        try {
            const body = createSchema.parse(req.body);
            const template = templates.find(t => t.id === body.templateId);
            if (!template)
                return res.status(400).json({ error: 'Template não encontrado' });
            const customer = await prisma_1.prisma.customer.findFirst({
                where: { id: body.customerId, storeId: req.storeId },
            });
            if (!customer)
                return res.status(404).json({ error: 'Cliente não encontrado' });
            const docData = {
                nome: customer.name,
                cpf: customer.cpf || '[NÃO INFORMADO]',
                telefone: customer.phone || '[NÃO INFORMADO]',
                email: customer.email || '[NÃO INFORMADO]',
                endereco: customer.address || '[NÃO INFORMADO]',
                data: new Date().toLocaleDateString('pt-BR'),
                ...(body.data || {}),
            };
            let content = template.content;
            for (const [key, value] of Object.entries(docData)) {
                content = content.replaceAll(`{{${key}}}`, String(value));
            }
            const doc = await prisma_1.prisma.document.create({
                data: {
                    customerId: body.customerId,
                    templateId: body.templateId,
                    category: body.category ? optimizer_1.Optimizer.normalizeCategory(body.category) : null,
                    data: JSON.stringify(docData),
                    content,
                    status: 'generated',
                },
            });
            return res.status(201).json({ ...doc, data: docData, content });
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Dados inválidos', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao criar documento' });
        }
    }
    async delete(req, res) {
        try {
            const doc = await prisma_1.prisma.document.findFirst({
                where: { id: req.params.id },
                include: { customer: true },
            });
            if (!doc || doc.customer.storeId !== req.storeId) {
                return res.status(404).json({ error: 'Documento não encontrado' });
            }
            await prisma_1.prisma.document.delete({ where: { id: doc.id } });
            return res.json({ message: 'Documento removido' });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao remover documento' });
        }
    }
}
exports.DocumentController = DocumentController;
//# sourceMappingURL=DocumentController.js.map