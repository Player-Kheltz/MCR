"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Optimizer = void 0;
class Optimizer {
    static normalizeName(name) {
        return name.trim()
            .replace(/\s+/g, ' ')
            .split(' ')
            .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
            .join(' ');
    }
    static normalizeCategory(name) {
        return name.trim()
            .replace(/\s+/g, ' ')
            .split(' ')
            .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
            .join(' ');
    }
    static normalizeEmail(email) {
        return email.trim().toLowerCase();
    }
    static normalizePhone(phone) {
        return phone.replace(/\D/g, '');
    }
    static normalizeDocument(doc) {
        return doc.replace(/\D/g, '');
    }
    static formatPrice(price) {
        return Math.round(price * 100) / 100;
    }
    static capitalizeWords(text) {
        return text.trim()
            .replace(/\s+/g, ' ')
            .split(' ')
            .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
            .join(' ');
    }
}
exports.Optimizer = Optimizer;
//# sourceMappingURL=optimizer.js.map