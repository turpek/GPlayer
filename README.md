# GPlayer

**GPlayer** é uma ferramenta avançada de processamento e edição de vídeo, desenvolvida em Python e OpenCV. Diferente de um player convencional, o GPlayer é focado na manipulação precisa de vídeos, permitindo navegação frame a frame, gerenciamento de seções e remoção de frames com funcionalidade de "desfazer".

Sua arquitetura é baseada em um sistema de duplo buffer (`BufferLeft` e `BufferRight`), que permite uma navegação eficiente tanto para frente (`proceed`) quanto para trás (`rewind`).

## ✨ Funcionalidades Principais

- **Navegação Frame a Frame:** Controle total sobre a reprodução, com a capacidade de avançar e retroceder quadro a quadro.
- **Gerenciamento de Seções:** Divida o vídeo em múltiplas seções, permitindo operações como:
  - **Dividir (`Split`):** Crie uma nova seção a partir do frame atual.
  - **Juntar (`Join`):** Mescle a seção atual com a anterior.
  - **Remover:** Exclua seções inteiras do vídeo.
  - **Navegar entre seções.**
- **Edição Não-Destrutiva:**
  - **Remoção de Frames:** Marque frames para serem removidos sem excluí-los permanentemente do arquivo original.
  - **Lixeira (`Trash`):** Um sistema de "lixeira" que armazena os frames removidos e permite restaurá-los (`undo`).
- **Controle de Velocidade:** Acelere ou desacelere a velocidade de reprodução.
- **Suporte a Playlist:** Carregue e navegue por uma lista de vídeos.
- **Persistência de Edições:** Salva o estado das seções e frames removidos em um arquivo `.json` associado ao vídeo.

## 🛠️ Tecnologias Utilizadas

- [Python 3](https://www.python.org/)
- [OpenCV (`opencv-python`)](https://pypi.org/project/opencv-python/): Para decodificação e exibição dos frames de vídeo.
- [Loguru](https://github.com/Delgan/loguru): Para logging.
- [NumPy](https://numpy.org/): Para manipulação de arrays de frames.

## 🚀 Instalação e Execução

**1. Clone o repositório:** ```bashgit clone [GitHub - turpek/GPlayer: Utiliza OpenCV para criar um buffer de frames de vídeo, permitindo controle eficiente de reprodução com funcionalidades de pausa e retrocesso de maneira fluida.](https://github.com/turpek/GPlayer.git)cd GPlayer

**2. Crie um ambiente virtual (recomendado):**

Bash

```bash
python -m venv venv
```

- No Windows: `venv\Scripts\activate`

- No Linux/macOS: `source venv/bin/activate`
  
  

**3. Instale as dependências:**

O projeto utiliza as bibliotecas listadas no arquivo requeriments.txt.

Bash

```bash
pip install -r requeriments.txt
```

**4. Execute o programa:**

Para iniciar, crie um script principal (ex: main.py) para instanciar e rodar a classe VideoCon.

Python

```python
# Exemplo de conteúdo para main.py

from src.video import VideoCon
from src.playlist import Playlist

if __name__ == '__main__':
    # Coloque o caminho para o seu vídeo aqui
    video_path = "caminho/para/seu/video.mp4"

    playlist = Playlist([video_path])

    with VideoCon(playlist) as video:
        while not video.quit():
            ret, frame = video.read()
            video.show(ret, frame)
```

Execute o script:

Bash

```
python main.py
```

## ⌨️ Comandos e Atalhos

A interação com o player é feita através de teclas na janela do OpenCV:

| Tecla        | Ação                     | Descrição                                                     |
| ------------ | ------------------------ | ------------------------------------------------------------- |
| **`d`**      | **Proceed**              | Ativa o modo de navegação para frente (padrão).               |
| **`a`**      | **Rewind**               | Ativa o modo de navegação para trás.                          |
| **`espaço`** | **Pause/Play (Delay)**   | Pausa a reprodução (delay=0) ou retoma à velocidade atual.    |
| **`b`**      | **Pause/Play (Toggle)**  | Pausa ou retoma a reprodução.                                 |
| **`x`**      | **Remover Frame**        | Remove o frame atual e o envia para a lixeira.                |
| **`u`**      | **Desfazer (Undo)**      | Restaura o último frame removido da lixeira.                  |
| **`[`**      | **Diminuir Velocidade**  | Aumenta o delay entre os frames.                              |
| **`]`**      | **Aumentar Velocidade**  | Diminui o delay entre os frames.                              |
| **`=`**      | **Restaurar Velocidade** | Volta para a velocidade de reprodução padrão.                 |
| **`s`**      | **Dividir Seção**        | Divide a seção atual no frame corrente.                       |
| **`c`**      | **Juntar Seção**         | Une a seção atual com a seção anterior.                       |
| **`r`**      | **Remover Seção**        | Remove a seção atual.                                         |
| **`y`**      | **Desfazer Seção**       | Restaura a última operação de seção (dividir/juntar/remover). |
| **`k`**      | **Próxima Seção**        | Pula para a próxima seção do vídeo.                           |
| **`j`**      | **Seção Anterior**       | Volta para a seção anterior.                                  |
| **`n`**      | **Próximo Vídeo**        | Carrega o próximo vídeo da playlist.                          |
| **`p`**      | **Vídeo Anterior**       | Carrega o vídeo anterior da playlist.                         |
| **`q`**      | **Sair**                 | Encerra o programa e salva o estado das seções.               |



### Diferença entre os Pauses Modos de Operação: Reprodução vs. Edição

O GPlayer foi projetado com dois modos distintos de pausa que definem a sua operação: um **Modo de Reprodução** e um **Modo de Edição**. Ao pressionar a tecla `espaço`, o programa entra no **Modo de Edição**, um estado de "pausa ativa" onde o vídeo congela, mas o sistema fica aguardando comandos. Isso permite a navegação precisa frame a frame com as teclas `a` e `d`, além de outras operações como remover (`x`) ou dividir (`s`) seções diretamente no quadro exibido. Em contrapartida, a tecla `b` ativa um pause de reprodução convencional, que simplesmente interrompe o fluxo do vídeo para visualização, sem permitir a mesma interatividade para manipulação dos frames.



## 💡 Conceitos do Projeto

- **`FrameMapper`**: Uma estrutura de dados central que mapeia todos os frames válidos que devem ser exibidos, excluindo os que foram removidos ou estão em `blacklists`.

- **`PlayerControl`**: Orquestra a lógica de navegação, alternando entre os buffers `VideoBufferLeft` (para `rewind`) e `VideoBufferRight` (para `proceed`).

- **`SectionManager`**: Gerencia o ciclo de vida das seções de um vídeo. As operações de edição (dividir, juntar, remover) são controladas aqui. O estado das seções é salvo em um arquivo `.json` para persistência.

- **`Trash`**: Implementa o padrão Memento para permitir que a remoção de frames possa ser desfeita.

# 
