"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.documentRoutes = void 0;
const express_1 = require("express");
const DocumentController_1 = require("../controllers/DocumentController");
const auth_1 = require("../middleware/auth");
const router = (0, express_1.Router)();
exports.documentRoutes = router;
const controller = new DocumentController_1.DocumentController();
router.use(auth_1.authMiddleware);
router.get('/templates', controller.listTemplates.bind(controller));
router.get('/', controller.list.bind(controller));
router.get('/:id', controller.getById.bind(controller));
router.post('/', controller.create.bind(controller));
router.delete('/:id', controller.delete.bind(controller));
//# sourceMappingURL=documents.js.map