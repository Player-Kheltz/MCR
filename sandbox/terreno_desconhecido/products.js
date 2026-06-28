"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.productRoutes = void 0;
const express_1 = require("express");
const multer_1 = __importDefault(require("multer"));
const ProductController_1 = require("../controllers/ProductController");
const auth_1 = require("../middleware/auth");
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const upload = (0, multer_1.default)({
    dest: 'uploads/',
    limits: { fileSize: 5 * 1024 * 1024 },
    fileFilter: (_req, file, cb) => {
        if (IMAGE_TYPES.includes(file.mimetype))
            cb(null, true);
        else
            cb(new Error('Apenas imagens (JPEG, PNG, WebP, GIF) são permitidas'));
    },
});
const router = (0, express_1.Router)();
exports.productRoutes = router;
const controller = new ProductController_1.ProductController();
router.use(auth_1.authMiddleware);
router.get('/', controller.list.bind(controller));
router.get('/:id', controller.getById.bind(controller));
router.post('/', upload.array('photos', 10), controller.create.bind(controller));
router.put('/:id', upload.array('photos', 10), controller.update.bind(controller));
router.delete('/:id', controller.delete.bind(controller));
//# sourceMappingURL=products.js.map