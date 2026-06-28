import { Response } from 'express';
import { AuthRequest } from '../middleware/auth';
export declare class PostController {
    list(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    getById(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    create(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    publish(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    update(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
    delete(req: AuthRequest, res: Response): Promise<Response<any, Record<string, any>>>;
}
//# sourceMappingURL=PostController.d.ts.map