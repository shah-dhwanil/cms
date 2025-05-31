import { RainbowButton } from "~/components/magicui/rainbow-button";
import Autoplay from "embla-carousel-autoplay";
import { ChevronDown} from "lucide-react";
import { Avatar, AvatarImage } from "~/components/shadcn/avatar";
import { Button } from "~/components/shadcn/button";
import { Carousel, CarouselContent, CarouselItem} from "~/components/shadcn/carousel";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "~/components/shadcn/dropdown-menu";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "~/components/shadcn/accordion";

export default function HomePage() {
    return (
      <>
      <main className="flex flex-col">
        <Carousel id="carousel" opts={{loop:true}} plugins={[Autoplay({delay:10000,playOnInit:true,jump:false})]}>
            <CarouselContent className="">
                <CarouselItem className="w-full h-screen">
                    <img src = "https://images.unsplash.com/photo-1618255630366-f402c45736f6" className="w-full h-full object-cover"/> 
                </CarouselItem>
                <CarouselItem className="w-full h-screen">
                    <img src = "https://images.unsplash.com/20/cambridge.JPG" className="w-full h-full object-cover"/>
                </CarouselItem>
            </CarouselContent>
        </Carousel>
        <div className="absolute inset-0 flex items-end justify-end mb-20 pr-24 z-10 pointer-events-none">
            <div className="text-right text-black pointer-events-none">
                <h1 className="text-5xl font-semibold goblin-one-regular">Welcome to</h1>
                <h1 className="text-7xl font-bold goldman-bold">University of Waterloo</h1>
                <RainbowButton size="lg" className="mt-8 w-64">Apply Now</RainbowButton>
            </div>
        </div>
        <div className="fixed top-0 w-full px-16 mt-8 z-20">
{/* Suggested code may be subject to a license. Learn more: ~LicenseLog:3778878527. */}
            <div id="navbar" className="flex flex-row bg-secondary gap-2.5 h-12 rounded-lg px-4 justify-start items-center">
                <Avatar>
                    <AvatarImage src="https://galgotiacollege.edu//public/uploads/all/3106/phelosophy.jpeg"></AvatarImage>
                    <a href="./"></a>
                </Avatar>
                <h4 className="hidden md:inline whitespace-nowrap poppins font-semibold">
                    University of Waterloo
                </h4>
                <div className="w-0 md:w-full"></div>
                <div className="flex flex-row w-full xl:gap-2 items-center justify-around">
                    <Button variant="secondary" className="shadow-none hover:bg-background">About Us</Button>
                    <DropdownMenu modal={false}>
                    <DropdownMenuTrigger asChild>
                    <Button variant="secondary" className="shadow-none hover:bg-background">Academics <ChevronDown/></Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent 
                        className="border-none z-[9999]" 
                        align="start" 
                        sideOffset={4}
                        avoidCollisions={true}
                        collisionPadding={8}
                    >
                        <DropdownMenuItem className="hover:bg-background" onClick={()=>{alert("Clicked!!!!")}}>Profile</DropdownMenuItem>
                        <DropdownMenuItem className="hover:bg-background">Billing</DropdownMenuItem>
                        <DropdownMenuItem className="hover:bg-background">Team</DropdownMenuItem>
                        <DropdownMenuItem className="hover:bg-background">Subscription</DropdownMenuItem>
                    </DropdownMenuContent>
                    </DropdownMenu>
                    <Button variant="secondary" className="shadow-none hover:bg-background">Facilities</Button>
                    <Button variant="secondary" className="shadow-none hover:bg-background">Events</Button>
                    <Button variant="secondary" className="shadow-none hover:bg-background">Notices</Button>
                    <Button variant="secondary" className="shadow-none hover:bg-background">Contact Us</Button>
                </div>
                <div className="w-0 md:w-full"></div>
                <div className="w-16">
                    <Button variant="default" size="default" className="rounded-lg">Log In</Button>
                </div>
            </div>
        </div>
      </main>
      <div id="schools_details" className="mt-8 w-full">
            <h2 className="text-4xl font-bold text-center">
                Our Schools of Excelence
            </h2>
            <Accordion type="multiple" className="w-auto mx-48 my-8 bg-card rounded-3xl">
                <AccordionItem className="rounded-2xl px-8" value="item-1">
                    <AccordionTrigger className="text-extrabold text-lg">Product Information</AccordionTrigger>
                    <AccordionContent className="flex flex-col gap-4 text-balance">
                    <p>
                        Our flagship product combines cutting-edge technology with sleek
                        design. Built with premium materials, it offers unparalleled
                        performance and reliability.
                    </p>
                    <p>
                        Key features include advanced processing capabilities, and an
                        intuitive user interface designed for both beginners and experts.
                    </p>
                    </AccordionContent>
                </AccordionItem>
                <AccordionItem className="rounded-2xl px-8" value="item-2">
                    <AccordionTrigger className="text-extrabold text-lg">Product Information</AccordionTrigger>
                    <AccordionContent className="flex flex-col gap-4 text-balance">
                    <p>
                        Our flagship product combines cutting-edge technology with sleek
                        design. Built with premium materials, it offers unparalleled
                        performance and reliability.
                    </p>
                    <p>
                        Key features include advanced processing capabilities, and an
                        intuitive user interface designed for both beginners and experts.
                    </p>
                    </AccordionContent>
                </AccordionItem>
                <AccordionItem className="rounded-2xl px-8" value="item-3">
                    <AccordionTrigger className="text-extrabold text-lg">Product Information</AccordionTrigger>
                    <AccordionContent className="flex flex-col gap-4 text-balance">
                    <p>
                        Our flagship product combines cutting-edge technology with sleek
                        design. Built with premium materials, it offers unparalleled
                        performance and reliability.
                    </p>
                    <p>
                        Key features include advanced processing capabilities, and an
                        intuitive user interface designed for both beginners and experts.
                    </p>
                    </AccordionContent>
                </AccordionItem>
            </Accordion>        
        </div>
        <div id="testimonials" className="my-8 w-full">
            <h2 className="text-4xl font-bold text-center">
                Testimonials
            </h2>
        </div>
      </>
      
    );
  }