-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema videogames_schema
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema videogames_schema
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `videogames_schema` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `videogames_schema` ;

-- -----------------------------------------------------
-- Table `videogames_schema`.`users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `videogames_schema`.`users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(255) NOT NULL,
  `last_name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `password` VARCHAR(255) NULL DEFAULT NULL,
  `avatar_url` VARCHAR(255) NULL DEFAULT NULL,
  `google_id` VARCHAR(255) NULL DEFAULT NULL,
  `facebook_id` VARCHAR(255) NULL DEFAULT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `email` (`email` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `videogames_schema`.`videogames`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `videogames_schema`.`videogames` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(255) NOT NULL,
  `description` TEXT NOT NULL,
  `system` VARCHAR(45) NOT NULL,
  `image_url` VARCHAR(255) NULL DEFAULT NULL,
  `video_url` VARCHAR(255) NULL DEFAULT NULL,
  `user_id` INT NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `user_id` (`user_id` ASC) VISIBLE,
  CONSTRAINT `videogames_ibfk_1`
    FOREIGN KEY (`user_id`)
    REFERENCES `videogames_schema`.`users` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 20
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `videogames_schema`.`favorites`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `videogames_schema`.`favorites` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `videogame_id` INT NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `user_id` (`user_id` ASC) VISIBLE,
  INDEX `videogame_id` (`videogame_id` ASC) VISIBLE,
  CONSTRAINT `favorites_ibfk_1`
    FOREIGN KEY (`user_id`)
    REFERENCES `videogames_schema`.`users` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `favorites_ibfk_2`
    FOREIGN KEY (`videogame_id`)
    REFERENCES `videogames_schema`.`videogames` (`id`)
    ON DELETE CASCADE)
ENGINE = InnoDB
AUTO_INCREMENT = 44
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
