import {
 IsEmail,
 IsEnum,
 IsString,
 MinLength
} from 'class-validator';


import { Role } from '@prisma/client';



export class RegisterDto {


@IsString()

name:string;



@IsEmail()

email:string;



@MinLength(6)

password:string;



@IsEnum(Role)

role:Role;


}