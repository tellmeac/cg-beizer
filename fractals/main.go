package main

import (
	"flag"
	"fmt"
	"math"

	"github.com/Pitrified/go-turtle"
)

// Nice images:
// go run main.go -f dragon -l 12 -i 4K
// go run main.go -f hilbert -l 7 -i 4K
// go run main.go -f sierpTri -l 7 -i 4K
func main() {
	which := flag.String("f", "hilbert", "Type of fractal to generate.")
	imgShape := flag.String("i", "4K", "Shape of the image to generate.")
	level := flag.Int("l", 4, "Recursion level to reach.")
	flag.Parse()
	drawFractals(*which, *imgShape, *level)
}

func drawFractals(which, imgShape string, level int) {
	var imgWidth, imgHeight float64
	var startX, startY, startD float64

	switch imgShape {
	case "4K":
		imgWidth = 1920 * 2
		imgHeight = 1080 * 2
	case "1200":
		imgWidth = 1200
		imgHeight = 1200
	}

	// receive the instructions here
	instructions := make(chan turtle.Instruction)

	switch which {

	case "hilbert":
		// Расчет значения для изображения относительно заданной высоты
		pad := 80.0
		segLen := getHilbertSegmentLen(level-1, imgHeight-pad)
		hp := pad / 2
		startX = float64(imgWidth-imgHeight)/2 + hp
		startY = hp
		startD = 0
		go GenerateHilbert(level, instructions, segLen)

	case "dragon":
		segLen := 20.0
		startX = imgWidth / 2
		startY = imgHeight / 2
		go GenerateDragon(level, instructions, segLen)

	case "sierpTri":
		pad := 80.0
		hp := pad / 2
		startX = float64(imgWidth-imgHeight)/2 + hp + imgHeight - pad
		startY = (imgHeight - (imgHeight-pad)*math.Sin(math.Pi/3)) / 2
		startD = 180.0
		segLen := (imgHeight - pad) / math.Exp2(float64(level))
		go GenerateSierpinskiTriangle(level, instructions, segLen)
	case "tree":
		segLen := 20.0
		startX = imgWidth / 2
		startY = 0.34 * imgHeight
		startD = 90

		// create a new world to draw in
		w := turtle.NewWorld(int(imgWidth), int(imgHeight))

		td := turtle.NewTurtleDraw(w)
		td.SetPos(startX, startY)
		td.SetHeading(startD)
		td.PenDown()
		td.SetColor(turtle.White)

		GenerateTree(level, td, segLen)

		outImgName := fmt.Sprintf("%s_%02d_%s.png", which, level, imgShape)
		_ = w.SaveImage(outImgName)

		return
	}

	// create a new world to draw in
	w := turtle.NewWorld(int(imgWidth), int(imgHeight))

	td := turtle.NewTurtleDraw(w)
	td.SetPos(startX, startY)
	td.SetHeading(startD)
	td.PenDown()
	td.SetColor(turtle.White)

	// draw the fractal
	for i := range instructions {
		td.DoInstruction(i)
	}

	outImgName := fmt.Sprintf("%s_%02d_%s.png", which, level, imgShape)
	_ = w.SaveImage(outImgName)
}

func getHilbertSegmentLen(level int, size float64) float64 {
	return size / (math.Exp2(float64(level-1))*4 - 1)
}

type Save struct {
	X     float64
	Y     float64
	Angle float64
}

// InstructionsWithSave supports [, ] in axioms for L-systems.
func InstructionsWithSave(
	level int,
	td *turtle.TurtleDraw,
	remaining string,
	rules map[byte]string,
	angle float64,
	forward float64,
	saves []Save,
) string {
	for len(remaining) > 0 {
		curChar := remaining[0]
		remaining = remaining[1:]

		fmt.Printf("%3d %c %+v\n", level, curChar, remaining)

		switch curChar {
		case '|':
			return remaining
		case '[':
			saves = append(saves, Save{
				X:     td.X,
				Y:     td.Y,
				Angle: td.Deg,
			})
		case ']':
			if len(saves) == 0 {
				panic("Possibly wrong axiom, expected to have checkpoint to recover for ']'")
			}
			s := saves[len(saves)-1]
			saves = saves[:len(saves)-1]

			td.SetPos(s.X, s.Y)
			td.SetHeading(s.Angle)
		case '+':
			td.DoInstruction(turtle.Instruction{Cmd: turtle.CmdLeft, Amount: angle})
		case '-':
			td.DoInstruction(turtle.Instruction{Cmd: turtle.CmdRight, Amount: angle})
		case 'F':
			td.DoInstruction(turtle.Instruction{Cmd: turtle.CmdForward, Amount: forward})
		case 'A', 'B':
			if level > 0 {
				remaining = rules[curChar] + "|" + remaining
				remaining = InstructionsWithSave(level-1, td, remaining, rules, angle, forward, saves)
			}
		case 'X', 'Y':
			if level == 0 {
				td.DoInstruction(turtle.Instruction{Cmd: turtle.CmdForward, Amount: forward})
			} else if level > 0 {
				remaining = rules[curChar] + "|" + remaining
				remaining = InstructionsWithSave(level-1, td, remaining, rules, angle, forward, saves)
			}
		}
	}

	return ""
}

// Instructions generates instructions for a general L-system.
func Instructions(
	level int,
	instructions chan<- turtle.Instruction,
	remaining string,
	rules map[byte]string,
	angle float64,
	forward float64,
) string {
	for len(remaining) > 0 {
		curChar := remaining[0]
		remaining = remaining[1:]

		fmt.Printf("%3d %c %+v\n", level, curChar, remaining)

		switch curChar {
		case '|':
			return remaining
		case '+':
			instructions <- turtle.Instruction{Cmd: turtle.CmdLeft, Amount: angle}
		case '-':
			instructions <- turtle.Instruction{Cmd: turtle.CmdRight, Amount: angle}
		// move forward explicitly when an 'F' is encountered
		case 'F':
			instructions <- turtle.Instruction{Cmd: turtle.CmdForward, Amount: forward}
		case 'A', 'B':
			if level > 0 {
				remaining = rules[curChar] + "|" + remaining
				remaining = Instructions(level-1, instructions, remaining, rules, angle, forward)
			}
		// move forward when the base of the recursion is reached
		case 'X', 'Y':
			if level == 0 {
				instructions <- turtle.Instruction{Cmd: turtle.CmdForward, Amount: forward}
			} else if level > 0 {
				remaining = rules[curChar] + "|" + remaining
				remaining = Instructions(level-1, instructions, remaining, rules, angle, forward)
			}
		}
	}

	close(instructions)
	return ""
}

// GenerateHilbert
// https://en.wikipedia.org/wiki/Hilbert_curve#Representation_as_Lindenmayer_system
func GenerateHilbert(level int, instructions chan<- turtle.Instruction, forward float64) {
	rules := map[byte]string{'A': "+BF-AFA-FB+", 'B': "-AF+BFB+FA-"}
	Instructions(level, instructions, "A", rules, 90, forward)
}

// GenerateDragon
// https://en.wikipedia.org/wiki/L-system#Example_6:_Dragon_curve
func GenerateDragon(level int, instructions chan<- turtle.Instruction, forward float64) {
	rules := map[byte]string{'X': "X+Y", 'Y': "X-Y"}
	Instructions(level, instructions, "X", rules, 90, forward)
}

// GenerateSierpinskiTriangle
// https://en.wikipedia.org/wiki/L-system#Example_5:_Sierpinski_triangle
func GenerateSierpinskiTriangle(level int, instructions chan<- turtle.Instruction, forward float64) {
	rules := map[byte]string{'X': "X-Y+X+Y-X", 'Y': "YY"}
	Instructions(level, instructions, "X-Y-Y", rules, 120, forward)
}

func GenerateTree(level int, td *turtle.TurtleDraw, forward float64) {
	rules := map[byte]string{'X': "X[+X]X[-X][X]"}
	InstructionsWithSave(level, td, "X", rules, forward, 25.7, nil)
}
