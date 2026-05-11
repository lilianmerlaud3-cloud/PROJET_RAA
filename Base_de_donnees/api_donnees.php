<?php
header("Content-Type: application/json; charset=utf-8");
header("Access-Control-Allow-Origin: *"); // En prod : remplacer * par le domaine du front
header("Access-Control-Allow-Methods: GET");

$host     = "127.0.0.1";
$dbname   = "test";
$username = "root";
$password = "";

try {
    $pdo = new PDO(
        "mysql:host=$host;port=3306;dbname=$dbname;charset=utf8mb4",
        $username,
        $password,
        [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
    );

    $sql = "SELECT 
                numero_arrete,
                date_acte,
                fonction_signataire,
                base_legale,
                objet
            FROM raa
            ORDER BY date_acte DESC";

    $stmt      = $pdo->query($sql);
    $resultats = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $donnees = [];

    foreach ($resultats as $ligne) {
        // Gestion du NULL sur objet
        $objet = !empty($ligne["objet"]) ? $ligne["objet"] : "objet non renseigné";

        $donnees[] = [
            "date"          => $ligne["date_acte"],          // Format YYYY-MM-DD (SQL natif)
            "auteur"        => $ligne["fonction_signataire"],
            "base_legale"   => $ligne["base_legale"],
            "numero_arrete" => $ligne["numero_arrete"],       // Champ séparé (plus de regex côté JS)
            "objet"         => $objet,                        // Champ séparé
            "contenu"       => "Arrêté n°" . $ligne["numero_arrete"] . " relatif à " . $objet . "."
        ];
    }

    http_response_code(200);
    echo json_encode([
        "success"      => true,
        "count"        => count($donnees),
        "raa_exemples" => $donnees
    ], JSON_UNESCAPED_UNICODE);

} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        "success"      => false,
        "raa_exemples" => [],
        // En prod : remplacer par un message générique sans getMessage()
        "erreur"       => "Erreur de base de données : " . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}
?>
