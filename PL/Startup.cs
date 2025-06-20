using BLL.IPersonReposatores;
using BLL.PersonReposatores;
using DAL.AppDbContext;
using DAL.Entity;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.HttpsPolicy;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using PL.MappingProfile;
using System;

namespace PL
{
    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }

        // This method gets called by the runtime. Use this method to add services to the container.
        public void ConfigureServices(IServiceCollection services)
        {
            services.AddControllersWithViews();

            // Registering UnitOfWork
            services.AddScoped<IUnitOfWork, UnitOfWork>();

            // Adding AutoMapper profiles
            services.AddAutoMapper(config =>
            {
                config.AddProfile(new PersonsProfile());
                config.AddProfile(new FatherProfile());
                config.AddProfile(new MotherProfile());
                config.AddProfile(new UserProfile());
                config.AddProfile(new RoleProfile());
            });

            // Configuring DbContext
            services.AddDbContext<AppDbContextClass>(options =>
            {
                options.UseSqlServer(Configuration.GetConnectionString("DefaultConnection"));
            });

            // Configuring Identity
            services.AddIdentity<ApplicationUser, IdentityRole>(options =>
            {
                options.Password.RequireNonAlphanumeric = true;
                options.Password.RequireDigit = true;
                options.Password.RequireUppercase = true;
                // options.Password.RequiredLength = 16; // Uncomment if you want to set a required length
            })
            .AddEntityFrameworkStores<AppDbContextClass>()
            .AddDefaultTokenProviders();

            // Configuring Cookie Authentication
            services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
                .AddCookie(options =>
                {
                    options.LoginPath = "/Account/Login"; // Add leading slash
                    options.AccessDeniedPath = "/Home/Error"; // Add leading slash
                });
        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }
            else
            {
                app.UseExceptionHandler("/Home/Error");
                app.UseHsts();
            }

            app.UseHttpsRedirection();
            app.UseStaticFiles();

            app.UseRouting();

            app.UseAuthentication();
            app.UseAuthorization();

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapControllerRoute(
                    name: "default",
                    pattern: "{controller=Home}/{action=Index}/{id?}");
            });
        }
    }
}
