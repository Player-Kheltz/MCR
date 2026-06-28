"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PostController = void 0;
const prisma_1 = require("../lib/prisma");
const zod_1 = require("zod");
const postSchema = zod_1.z.object({
    content: zod_1.z.string().min(1),
    productId: zod_1.z.string().optional(),
    platforms: zod_1.z.array(zod_1.z.string()).min(1),
    media: zod_1.z.array(zod_1.z.string()).optional(),
    scheduledAt: zod_1.z.string().optional(),
});
class PostController {
    async list(req, res) {
        try {
            const posts = await prisma_1.prisma.post.findMany({
                where: { storeId: req.storeId },
                include: { product: { select: { id: true, name: true, photos: true } } },
                orderBy: { createdAt: 'desc' },
            });
            return res.json(posts.map(p => ({
                ...p,
                media: JSON.parse(p.media),
                platforms: JSON.parse(p.platforms),
                platformStatus: JSON.parse(p.platformStatus),
                product: p.product ? { ...p.product, photos: JSON.parse(p.product.photos) } : null,
            })));
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao listar postagens' });
        }
    }
    async getById(req, res) {
        try {
            const post = await prisma_1.prisma.post.findFirst({
                where: { id: req.params.id, storeId: req.storeId },
                include: { product: { select: { id: true, name: true, photos: true, price: true, description: true } } },
            });
            if (!post)
                return res.status(404).json({ error: 'Postagem não encontrada' });
            return res.json({
                ...post,
                media: JSON.parse(post.media),
                platforms: JSON.parse(post.platforms),
                platformStatus: JSON.parse(post.platformStatus),
                product: post.product ? { ...post.product, photos: JSON.parse(post.product.photos) } : null,
            });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao buscar postagem' });
        }
    }
    async create(req, res) {
        try {
            const data = postSchema.parse(req.body);
            const files = req.files;
            const media = files ? files.map(f => f.filename) : (data.media || []);
            if (data.productId) {
                const product = await prisma_1.prisma.product.findFirst({
                    where: { id: data.productId, storeId: req.storeId },
                });
                if (!product)
                    return res.status(400).json({ error: 'Produto não encontrado' });
            }
            const post = await prisma_1.prisma.post.create({
                data: {
                    storeId: req.storeId,
                    productId: data.productId || null,
                    content: data.content,
                    media: JSON.stringify(media),
                    platforms: JSON.stringify(data.platforms),
                    platformStatus: JSON.stringify(Object.fromEntries(data.platforms.map(p => [p, 'pending']))),
                    scheduledAt: data.scheduledAt ? new Date(data.scheduledAt) : null,
                    status: data.scheduledAt ? 'scheduled' : 'draft',
                },
            });
            return res.status(201).json({
                ...post,
                media: JSON.parse(post.media),
                platforms: JSON.parse(post.platforms),
                platformStatus: JSON.parse(post.platformStatus),
            });
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Dados inválidos', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao criar postagem' });
        }
    }
    async publish(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const post = await prisma_1.prisma.post.findFirst({ where: { id, storeId, status: { in: ['draft', 'scheduled'] } } });
            if (!post)
                return res.status(404).json({ error: 'Postagem não encontrada ou já publicada' });
            const platforms = JSON.parse(post.platforms);
            const status = {};
            for (const platform of platforms) {
                try {
                    status[platform] = await publishToPlatform(platform, post, storeId);
                }
                catch {
                    status[platform] = 'failed';
                }
            }
            const allSuccess = Object.values(status).every(s => s === 'published');
            const someFailed = Object.values(status).some(s => s === 'failed');
            const updated = await prisma_1.prisma.post.update({
                where: { id },
                data: {
                    platformStatus: JSON.stringify(status),
                    status: allSuccess ? 'published' : someFailed ? 'partial' : 'pending',
                    publishedAt: new Date(),
                },
            });
            return res.json({
                ...updated,
                media: JSON.parse(updated.media),
                platforms: JSON.parse(updated.platforms),
                platformStatus: JSON.parse(updated.platformStatus),
            });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao publicar' });
        }
    }
    async update(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.post.findFirst({ where: { id, storeId } });
            if (!existing)
                return res.status(404).json({ error: 'Postagem não encontrada' });
            if (existing.status === 'published' || existing.status === 'partial') {
                return res.status(400).json({ error: 'Não é possível editar uma postagem já publicada' });
            }
            const data = postSchema.partial().parse(req.body);
            const updateData = {};
            if (data.content !== undefined)
                updateData.content = data.content;
            if (data.productId !== undefined)
                updateData.productId = data.productId;
            if (data.platforms !== undefined)
                updateData.platforms = JSON.stringify(data.platforms);
            if (data.media !== undefined)
                updateData.media = JSON.stringify(data.media);
            if (data.scheduledAt !== undefined)
                updateData.scheduledAt = data.scheduledAt ? new Date(data.scheduledAt) : null;
            const updated = await prisma_1.prisma.post.update({ where: { id }, data: updateData });
            return res.json({
                ...updated,
                media: JSON.parse(updated.media),
                platforms: JSON.parse(updated.platforms),
                platformStatus: JSON.parse(updated.platformStatus),
            });
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Dados inválidos', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao atualizar postagem' });
        }
    }
    async delete(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.post.findFirst({ where: { id, storeId } });
            if (!existing)
                return res.status(404).json({ error: 'Postagem não encontrada' });
            await prisma_1.prisma.post.delete({ where: { id } });
            return res.json({ message: 'Postagem removida' });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao remover postagem' });
        }
    }
}
exports.PostController = PostController;
async function publishToPlatform(platform, post, storeId) {
    console.warn(`[${platform}] Publicacao simulada para post ${post.id} -- integracao real pendente`);
    switch (platform) {
        case 'instagram':
        case 'facebook':
        case 'mercado_livre':
        case 'olx':
            return 'pending';
        default:
            return 'pending';
    }
}
//# sourceMappingURL=PostController.js.map