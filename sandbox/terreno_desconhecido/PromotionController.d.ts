import { Response } from 'express';
import { AuthRequest } from '../middleware/auth';
export declare class PromotionController {
    list(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    active(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    getById(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    create(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    update(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    activate(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    delete(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
}
//# sourceMappingURL=PromotionController.d.ts.map