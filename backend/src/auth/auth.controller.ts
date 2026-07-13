import {
Body,
Controller,
Post
} from '@nestjs/common';


import { AuthService } from './auth.service';


import { RegisterDto } from './dto/register.dto';


import { LoginDto } from './dto/login.dto';



@Controller('auth')

export class AuthController {


constructor(
private service:AuthService
){}



@Post('register')

register(
@Body() data:RegisterDto
){

return this.service.register(data);

}




@Post('login')

login(
@Body() data:LoginDto
){

return this.service.login(data);

}


}