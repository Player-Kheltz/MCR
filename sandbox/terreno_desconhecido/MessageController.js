"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MessageController = void 0;
const prisma_1 = require("../lib/prisma");
const zod_1 = require("zod");
const messageSchema = zod_1.z.object({
    customerId: zod_1.z.string().min(1),
    content: zod_1.z.string().min(1).max(500),
    channel: zod_1.z.string().optional(),
});
class MessageController {
    async conversations(req, res) {
        try {
            const storeId = req.storeId;
            const messages = await prisma_1.prisma.message.findMany({
                where: { storeId },
                include: { customer: { select: { id: true, name: true, phone: true, source: true } } },
                orderBy: { createdAt: 'desc' },
            });
            const grouped = {};
            for (const m of messages) {
                const cid = m.customerId;
                if (!grouped[cid]) {
                    grouped[cid] = {
                        customer: m.customer,
                        lastMessage: m.content,
                        lastDate: m.createdAt,
                        channel: m.channel,
                        count: 0,
                    };
                }
                grouped[cid].count++;
                if (m.createdAt > grouped[cid].lastDate) {
                    grouped[cid].lastMessage = m.content;
                    grouped[cid].lastDate = m.createdAt;
                }
            }
            return res.json(Object.values(grouped));
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao listar conversas' });
        }
    }
    async byCustomer(req, res) {
        try {
            const customerId = req.params.customerId;
            const storeId = req.storeId;
            const customer = await prisma_1.prisma.customer.findFirst({ where: { id: customerId, storeId } });
            if (!customer)
                return res.status(404).json({ error: 'Cliente nao encontrado' });
            const messages = await prisma_1.prisma.message.findMany({
                where: { customerId, storeId },
                orderBy: { createdAt: 'asc' },
            });
            return res.json({ customer, messages });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao buscar mensagens' });
        }
    }
    async send(req, res) {
        try {
            const data = messageSchema.parse(req.body);
            const storeId = req.storeId;
            const customer = await prisma_1.prisma.customer.findFirst({ where: { id: data.customerId, storeId } });
            if (!customer)
                return res.status(404).json({ error: 'Cliente nao encontrado' });
            const msg = await prisma_1.prisma.message.create({
                data: {
                    storeId,
                    customerId: data.customerId,
                    content: data.content,
                    channel: data.channel || 'interno',
                    direction: 'sent',
                },
            });
            return res.status(201).json(msg);
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError)
                return res.status(400).json({ error: 'Dados invalidos' });
            console.error(err);
            return res.status(500).json({ error: 'Erro ao enviar mensagem' });
        }
    }
}
exports.MessageController = MessageController;
//# sourceMappingURL=MessageController.js.map