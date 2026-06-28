"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.customerRoutes = void 0;
const express_1 = require("express");
const CustomerController_1 = require("../controllers/CustomerController");
const auth_1 = require("../middleware/auth");
const router = (0, express_1.Router)();
exports.customerRoutes = router;
const controller = new CustomerController_1.CustomerController();
router.use(auth_1.authMiddleware);
router.get('/', controller.list.bind(controller));
router.get('/:id', controller.getById.bind(controller));
router.post('/', controller.create.bind(controller));
router.put('/:id', controller.update.bind(controller));
router.delete('/:id', controller.delete.bind(controller));
//# sourceMappingURL=customers.js.map