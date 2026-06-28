"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.categoryRoutes = void 0;
const express_1 = require("express");
const CategoryController_1 = require("../controllers/CategoryController");
const auth_1 = require("../middleware/auth");
const router = (0, express_1.Router)();
exports.categoryRoutes = router;
const controller = new CategoryController_1.CategoryController();
router.use(auth_1.authMiddleware);
router.get('/', controller.list.bind(controller));
router.post('/', controller.create.bind(controller));
router.post('/merge', controller.merge.bind(controller));
router.delete('/:id', controller.delete.bind(controller));
//# sourceMappingURL=categories.js.map