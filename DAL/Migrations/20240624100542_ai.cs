using Microsoft.EntityFrameworkCore.Migrations;

namespace DAL.Migrations
{
    public partial class ai : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "ImageNameAI",
                table: "Persons",
                type: "nvarchar(max)",
                nullable: true);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ImageNameAI",
                table: "Persons");
        }
    }
}
