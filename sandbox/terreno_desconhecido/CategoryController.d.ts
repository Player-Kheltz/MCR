import { Response } from 'express';
import { AuthRequest } from '../middleware/auth';
export declare class CategoryController {
    list(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    create(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    delete(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    merge(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
}
//# sourceMappingURL=CategoryController.d.ts.map