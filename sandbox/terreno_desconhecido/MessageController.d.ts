import { Response } from 'express';
import { AuthRequest } from '../middleware/auth';
export declare class MessageController {
    conversations(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    byCustomer(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    send(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
}
//# sourceMappingURL=MessageController.d.ts.map