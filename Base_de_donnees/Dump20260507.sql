-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: mabdd
-- ------------------------------------------------------
-- Server version	5.5.5-10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `raa`
--

DROP TABLE IF EXISTS `raa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `raa` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `numero_arrete` varchar(50) NOT NULL,
  `date_acte` date NOT NULL,
  `fonction_signataire` varchar(200) NOT NULL,
  `base_legale` text NOT NULL,
  `prefecture` varchar(100) NOT NULL,
  `objet` text NOT NULL,
  `texte_brut` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero_arrete` (`numero_arrete`),
  KEY `idx_raa_date` (`date_acte`),
  KEY `idx_raa_prefecture` (`prefecture`)
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `raa`
--

LOCK TABLES `raa` WRITE;
/*!40000 ALTER TABLE `raa` DISABLE KEYS */;
INSERT INTO `raa` VALUES (49,'2024-44','2024-04-29','Le préfet','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-44 du 29 avril 2024 portant autorisation d\'un système de vidéoprotection  === CONSIDERANTS ===  Considérant que ce lieu est particulièrement exposé à des risques d\'agression ou de vol ; Considérant le caractère proportionné du nombre de caméras envisagées au regard des risques susmentionnés ; ARRÊTE  === ARTICLES ===  Article 1 — Monsieur SAMIR MCHICHI est autorisé, dans les conditions fixées au présent arrêté et pour une durée de cinq ans renouvelable, à installer 4 caméras intérieures et 4 caméras extérieures de vidéoprotection au sein de l\'établissement Association des Musulmans de Cherbourg 46 rue Coluche 50130 CHERBOURG-EN-COTENTIN, conformément au dossier présenté et annexé à la demande enregistrée sous le numéro 2024/0087. Signé : Le préfet : M. Xavier brunetière'),(50,'2024-56','2024-05-21','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-56 du 21 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur THOMAS VELTER est autorisé à installer des caméras extérieures en périmètre vidéoprotégé au sein du périmètre géographique dite « zone verte » de l\'etablissement PUBLIC DU MONT SAINT MICHEL. Signé : pour le préfet et par délégation, Le sous-préfet d\'Avranches : M. Pierre CHAULEUR'),(51,'2024-61','2024-05-21','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-61 du 21 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur Jacques BONO, maire du Mont-Saint-Michel, est autorisé à installer 50 caméras voie publique de vidéoprotection au sein de la COMMUNE de LE MONT-SAINT-MICHEL. Signé : M. Pierre CHAULEUR'),(52,'2024-65','2024-05-21','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-65 du 21 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur MARTIAL CHABRERIE, directeur Kéolis Mont-Saint-Michel, est autorisé à installer 60 caméras intérieures de vidéoprotection au sein des véhicules de transport public appartenant à KEOLIS MONT-SAINT-MICHEL. Signé : M. Pierre CHAULEUR'),(53,'2024-46','2024-05-23','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-46 du 23 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur Stéphane LECOURT est autorisé à installer 3 caméras intérieures et 1 caméra extérieure de vidéoprotection au sein de l\'établissement Sarl Camping de l\'Espérance 36 rue de la Gamburie - Denneville 50580 PORT-BAIL-SUR-MER. Signé : M. Pierre CHAULEUR'),(54,'2024-47','2024-05-23','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-47 du 23 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Madame Caroline Boullot est autorisée à installer 3 caméras intérieures de vidéoprotection au sein de l\'établissement SELARL pharmacie du parvis 2 rue geoffroy de montbray 50200 COUTANCES. Signé : M. Pierre CHAULEUR'),(55,'2024-51','2024-05-23','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-51 du 23 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur DIDIER DEHENT est autorisé à installer 2 caméras extérieures de vidéoprotection au sein de l\'établissement Mondial Relay-Consigne N° 28720 1 rue des Carrières Saint-Michel 50200 SAINT-PIERRE-DE-COUTANCES. Signé : M. Pierre CHAULEUR'),(56,'2024-52','2024-05-23','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-52 du 23 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Madame Adeline Cantrel est autorisée à installer 2 caméras intérieures de vidéoprotection au sein de l\'établissement SARL restaurant du château 16 rue Du château 50250 LA HAYE. Signé : M. Pierre CHAULEUR'),(57,'2024-53','2024-05-23','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-53 du 23 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Madame Martine LOUVEAU est autorisée à installer 2 caméras intérieures et 2 caméras extérieures de vidéoprotection au sein de l\'établissement Ligue de l\'enseignement de Normandie 88 rue du pont bleu 50380 SAINT-PAIR-SUR-MER. Signé : M. Pierre CHAULEUR'),(58,'2024-54','2024-05-23','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-54 du 23 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur BRUNO CHOINARD est autorisé à installer 6 caméras intérieures et 2 caméras extérieures de vidéoprotection au sein de l\'établissement SCS LA coutancaise 4 allée du Château de la Mare 50200 COUTANCES. Signé : M. Pierre CHAULEUR'),(59,'2024-55','2024-05-23','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-55 du 23 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur Valéry BAUCHARD est autorisé à installer 2 caméras extérieures de vidéoprotection au sein de l\'établissement CARGILL FRANCE - Site Baupte 50500 BAUPTE. Signé : M. Pierre CHAULEUR'),(60,'2024-59','2024-05-27','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-59 du 27 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur Quentin BENAULT est autorisé à installer 2 caméras extérieures de vidéoprotection au sein de l\'établissement Mondial Relay - Consigne N° 023758 rue Cornu 50360 PICAUVILLE. Signé : M. Pierre CHAULEUR'),(61,'2024-60','2024-05-27','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-60 du 27 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur Quentin BENAULT est autorisé à installer 2 caméras extérieures de vidéoprotection au sein de l\'établissement Mondial relay - N° 23210 6 La Richardière 59600 SAINT-HILAIRE-DU-HARCOUET. Signé : M. Pierre CHAULEUR'),(62,'2024-62','2024-05-27','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-62 du 27 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur PATRICE BODENAN est autorisé à installer 7 caméras intérieures de vidéoprotection au sein de l\'établissement SARL GRIZCKLES 79 rue Waldeck Rousseau 50600 SAINT-HILAIRE-DU-HARCOUET. Signé : M. Pierre CHAULEUR'),(63,'2024-63','2024-05-27','pour le préfet et par délégation, Le sous-préfet d\'Avranches','desquelles cette autorisation a été délivrée.','','autorisation d\'un système de vidéoprotection','Arrêté n° 2024-63 du 27 mai 2024 portant autorisation d\'un système de vidéoprotection  Article 1 — Monsieur Laurent Pien est autorisé à installer 2 caméras extérieures de vidéoprotection au sein de l\'établissement Syndicat Mixte du Point Fort Hôtel Bled 50620 CAVIGNY. Signé : M. Pierre CHAULEUR');
/*!40000 ALTER TABLE `raa` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-07 16:06:30
