import {
 Injectable,
 UnauthorizedException
} from '@nestjs/common';


import { PrismaService } from '../prisma/prisma.service';


import * as bcrypt from 'bcrypt';


import { JwtService } from '@nestjs/jwt';


import { RegisterDto } from './dto/register.dto';


import { LoginDto } from './dto/login.dto';



@Injectable()

export class AuthService {


constructor(

private prisma:PrismaService,

private jwt:JwtService

){}



async register(data:RegisterDto){


const passwordHash = await bcrypt.hash(
data.password,
10
);



const user = await this.prisma.user.create({

data:{

name:data.name,

email:data.email,

password:passwordHash,

role:data.role

}

});



return {

id:user.id,

name:user.name,

email:user.email,

role:user.role

};


}





async login(data:LoginDto){


const user =
await this.prisma.user.findUnique({

where:{
email:data.email
}

});



if(!user)

throw new UnauthorizedException(
'Usuário não encontrado'
);



const valid =
await bcrypt.compare(
data.password,
user.password
);



if(!valid)

throw new UnauthorizedException(
'Senha inválida'
);



const token =
this.jwt.sign({

sub:user.id,

role:user.role

});



return {

access_token:token,

user:{

id:user.id,

name:user.name,

role:user.role

}

};


}


}