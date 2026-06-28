"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.messageRoutes = void 0;
const express_1 = require("express");
const MessageController_1 = require("../controllers/MessageController");
const auth_1 = require("../middleware/auth");
const router = (0, express_1.Router)();
exports.messageRoutes = router;
const controller = new MessageController_1.MessageController();
router.use(auth_1.authMiddleware);
router.get('/conversations', controller.conversations.bind(controller));
router.get('/:customerId', controller.byCustomer.bind(controller));
router.post('/', controller.send.bind(controller));
//# sourceMappingURL=messages.js.map