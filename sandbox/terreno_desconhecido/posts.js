"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.postRoutes = void 0;
const express_1 = require("express");
const multer_1 = __importDefault(require("multer"));
const PostController_1 = require("../controllers/PostController");
const auth_1 = require("../middleware/auth");
const MEDIA_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'video/mp4'];
const upload = (0, multer_1.default)({
    dest: 'uploads/',
    limits: { fileSize: 10 * 1024 * 1024 },
    fileFilter: (_req, file, cb) => {
        if (MEDIA_TYPES.includes(file.mimetype))
            cb(null, true);
        else
            cb(new Error('Apenas imagens e videos (MP4) são permitidos'));
    },
});
const router = (0, express_1.Router)();
exports.postRoutes = router;
const controller = new PostController_1.PostController();
router.use(auth_1.authMiddleware);
router.get('/', controller.list.bind(controller));
router.get('/:id', controller.getById.bind(controller));
router.post('/', upload.array('media', 10), controller.create.bind(controller));
router.put('/:id', upload.array('media', 10), controller.update.bind(controller));
router.post('/:id/publish', controller.publish.bind(controller));
router.delete('/:id', controller.delete.bind(controller));
//# sourceMappingURL=posts.js.map